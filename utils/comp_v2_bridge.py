"""
Components V2 bridge.

Converts legacy ``embed=`` / ``embeds=`` kwargs into a :class:`discord.ui.LayoutView`
containing :class:`discord.ui.Container` children so existing cog code never needs
to know about Components V2.

Each embed becomes one Container whose children are built in this order:

1. **Thumbnail** (``embed.thumbnail``) — a ``discord.ui.Section`` whose
   ``accessory`` is a ``discord.ui.Thumbnail`` (Discord requires thumbnails on
   sections), with title / description / fields / footer as the section body.
   ``embed.footer`` text is shown; footer ``icon_url`` is intentionally omitted
   (V2 ``TextDisplay`` does not mirror classic footer icons cleanly).
2. **Text** — without a thumbnail, one ``TextDisplay`` for the same markdown.
3. **Fields** — non-inline fields are stacked blocks; up to three consecutive
   **inline** fields share one row (name line + value line, `` · ``-separated).
4. **Main image** (``embed.image``) — a single-item ``discord.ui.MediaGallery``
   appended after the text block.
5. **Buttons / selects** from any accompanying ``view=`` — migrated out of the
   v1 :class:`discord.ui.View` into ``discord.ui.ActionRow`` items and appended
   inside the same Container so they are visually grouped with the embed content.

When a cog passes ``view=`` with a classic :class:`discord.ui.View`, the bridge
consumes it and folds its components into the Container.  The original ``view=``
is replaced by the new ``LayoutView``.
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional, Sequence

import discord

# Pass as a keyword to patched ``send`` / ``send_message`` / ``edit`` /
# ``edit_message`` to keep classic embeds + v1 components (no LayoutView).
# Stripped before the real discord.py coroutine runs.
SKIP_COMPONENTS_V2_BRIDGE = "_cv2_skip"

__all__ = [
    "enable_components_v2_embed_bridge",
    "is_patched",
    "SKIP_COMPONENTS_V2_BRIDGE",
    "interaction_send_message_without_cv2_bridge",
    "message_edit_without_cv2_bridge",
]

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal state
# ---------------------------------------------------------------------------

_PATCHED = False

# Pre-monkeypatch callables (set when each method is wrapped). Used to bypass
# the bridge for flows that must stay classic embed + v1 components — e.g. select
# menus that edit ``interaction.message`` (a plain :class:`discord.Message` whose
# ``edit`` is patched).
_ORIGINAL_INTERACTION_RESPONSE_SEND_MESSAGE: Any = None
_ORIGINAL_MESSAGE_EDIT: Any = None

# Resolved once at enable-time so every hot-path avoids repeated getattr calls.
_LayoutView: type | None = None
_Container: type | None = None
_TextDisplay: type | None = None
_Section: type | None = None
_MediaGallery: type | None = None
_MediaGalleryItem: type | None = None
_Thumbnail: type | None = None
_UnfurledMediaItem: type | None = None
_ActionRow: type | None = None
_MISSING: Any = None


def is_patched() -> bool:
    """Return ``True`` if the bridge has already been installed."""
    return _PATCHED


# ---------------------------------------------------------------------------
# Sentinel helpers
# ---------------------------------------------------------------------------

def _is_missing(value: Any) -> bool:
    """Return ``True`` for ``discord.utils.MISSING`` sentinels."""
    return _MISSING is not None and value is _MISSING


def _unwrap(value: Any, default: Any = None) -> Any:
    """Return *default* when *value* is ``None`` or ``MISSING``, else *value*."""
    if value is None or _is_missing(value):
        return default
    return value


# ---------------------------------------------------------------------------
# Embed helpers
# ---------------------------------------------------------------------------

def _peek_embeds(kwargs: dict) -> List[discord.Embed]:
    """Return the embed list without mutating *kwargs*."""
    out: List[discord.Embed] = []
    e = kwargs.get("embed")
    if isinstance(e, discord.Embed):
        out.append(e)
    es = kwargs.get("embeds")
    if es:
        out.extend(x for x in es if isinstance(x, discord.Embed))
    return out


def _pop_embeds(kwargs: dict) -> List[discord.Embed]:
    """Remove and return all embeds from *kwargs*."""
    out: List[discord.Embed] = []
    e = kwargs.pop("embed", None)
    if isinstance(e, discord.Embed):
        out.append(e)
    es = kwargs.pop("embeds", None)
    if es:
        out.extend(x for x in es if isinstance(x, discord.Embed))
    return out


def _embed_colour(embed: discord.Embed) -> Optional[int]:
    c = embed.color
    if c is None or _is_missing(c):
        return None
    return int(getattr(c, "value", c))


def _embed_image_url(embed: discord.Embed, attr: str) -> Optional[str]:
    """Return the URL for ``embed.image`` or ``embed.thumbnail``, or ``None``."""
    proxy = getattr(embed, attr, None)
    if proxy is None or _is_missing(proxy):
        return None
    url = getattr(proxy, "url", None)
    if not url or _is_missing(url):
        return None
    return url


def _embed_fields_to_markdown(fields: Sequence[Any]) -> str:
    """
    Embed fields as markdown: full-width blocks for ``inline=False``, and up to
    three ``inline=True`` fields per row (names on one line, values on the next).
    """
    if not fields:
        return ""

    parts: List[str] = []
    i = 0
    n = len(fields)
    while i < n:
        field = fields[i]
        if not getattr(field, "inline", True):
            name = (getattr(field, "name", None) or "").strip()
            value = (getattr(field, "value", None) or "")
            block: List[str] = []
            if name:
                block.append(f"**{name}**")
            if value:
                block.append(value)
            if block:
                parts.append("\n".join(block))
            i += 1
            continue

        row: List[Any] = []
        while i < n and getattr(fields[i], "inline", True) and len(row) < 3:
            row.append(fields[i])
            i += 1
        if not row:
            i += 1
            continue

        row_names: List[str] = []
        row_vals: List[str] = []
        for f in row:
            fn = (getattr(f, "name", None) or "").strip()
            fv = (getattr(f, "value", None) or "")
            fv_one = " ".join(fv.splitlines()).strip()
            row_names.append(f"**{fn}**" if fn else "\u200b")
            row_vals.append(fv_one if fv_one else "\u200b")

        if len(row) == 1:
            parts.append(f"{row_names[0]}\n{row_vals[0]}")
        else:
            parts.append(" · ".join(row_names))
            parts.append(" · ".join(row_vals))

    return "\n\n".join(parts)


def _embed_footer_markdown(embed: discord.Embed) -> str:
    """Footer subtext only (``embed.footer``); ``icon_url`` is never rendered as an image."""
    foot = getattr(embed, "footer", None)
    if foot is None or _is_missing(foot):
        return ""
    text = getattr(foot, "text", None)
    if not text or _is_missing(text):
        return ""
    return f"-# {text}"


def _embed_to_markdown(embed: discord.Embed) -> str:
    """Render an :class:`discord.Embed` as discord-flavoured Markdown."""
    body_parts: List[str] = []

    if embed.title:
        body_parts.append(f"## {embed.title}")

    if embed.description:
        body_parts.append(embed.description.strip())

    field_md = _embed_fields_to_markdown(embed.fields)
    if field_md:
        body_parts.append(field_md)

    body = "\n\n".join(p for p in body_parts if p).strip()
    footer_md = _embed_footer_markdown(embed)
    if footer_md and body:
        # Keep footer visually attached to content; avoid an extra paragraph gap.
        return f"{body}\n{footer_md}".strip() or "\u200b"
    if footer_md:
        return footer_md.strip() or "\u200b"
    return body or "\u200b"


# ---------------------------------------------------------------------------
# Component V2 object builders
# ---------------------------------------------------------------------------

def _build_text_display(content: str) -> Any | None:
    """Instantiate a :class:`discord.ui.TextDisplay`."""
    if _TextDisplay is None:
        return None
    for args, kw in (
        ((), {"content": content}),
        ((content,), {}),
        ((), {"text": content}),
    ):
        try:
            return _TextDisplay(*args, **kw)
        except TypeError:
            continue
    log.warning("components_v2_bridge: TextDisplay — all signatures failed")
    return None


def _build_unfurled_media(url: str) -> Any | None:
    """
    Instantiate a :class:`discord.ui.UnfurledMediaItem` (the URL wrapper
    accepted by MediaGallery and Thumbnail).  Falls back to a plain string
    on older builds that accept raw URLs directly.
    """
    if _UnfurledMediaItem is not None:
        for args, kw in (
            ((url,), {}),
            ((), {"url": url}),
        ):
            try:
                return _UnfurledMediaItem(*args, **kw)
            except TypeError:
                continue
    # Some builds accept the raw URL string directly.
    return url


def _build_media_gallery(url: str) -> Any | None:
    """
    Build a single-item :class:`discord.ui.MediaGallery` for ``embed.image``.
    """
    if _MediaGallery is None:
        return None

    media = _build_unfurled_media(url)

    # Try wrapping in a MediaGalleryItem first (newer builds require it).
    item: Any = None
    if _MediaGalleryItem is not None:
        for args, kw in (
            ((media,), {}),
            ((), {"media": media}),
            ((), {"url": url}),
        ):
            try:
                item = _MediaGalleryItem(*args, **kw)
                break
            except TypeError:
                continue

    # Fall back: some builds accept raw UnfurledMediaItem directly — never a
    # bare str (MediaGalleryComponent.to_dict expects item.to_dict() per item).
    if item is None:
        item = media
    if isinstance(item, str) and _MediaGalleryItem is not None:
        try:
            item = _MediaGalleryItem(item)
        except TypeError:
            try:
                item = _MediaGalleryItem(media=item)
            except TypeError:
                pass
    if isinstance(item, str):
        log.warning(
            "components_v2_bridge: cannot build MediaGalleryItem for URL — skipping embed image"
        )
        return None

    for args, kw in (
        ((item,), {}),
        ((), {"items": [item]}),
        ((), {"children": [item]}),
    ):
        try:
            return _MediaGallery(*args, **kw)
        except TypeError:
            continue

    log.warning("components_v2_bridge: MediaGallery — all signatures failed for %s", url)
    return None


def _build_thumbnail(url: str) -> Any | None:
    """
    Build a :class:`discord.ui.Thumbnail` for ``embed.thumbnail``.
    Thumbnail is used as a Container *accessory* so it renders beside the text.
    """
    if _Thumbnail is None:
        return None

    media = _build_unfurled_media(url)

    for args, kw in (
        ((media,), {}),
        ((), {"media": media}),
        ((), {"url": url}),
    ):
        try:
            return _Thumbnail(*args, **kw)
        except TypeError:
            continue

    log.warning("components_v2_bridge: Thumbnail — all signatures failed for %s", url)
    return None


def _build_section_with_thumbnail(body_markdown: str, thumbnail_url: str) -> Any | None:
    """
    Build a :class:`discord.ui.Section` with body text and a ``Thumbnail`` accessory.
    Thumbnails are only valid as a Section accessory in the v2 component kit.
    """
    if _Section is None or _Thumbnail is None:
        return None
    thumb = _build_thumbnail(thumbnail_url)
    if thumb is None:
        return None
    text = body_markdown.strip() or "\u200b"
    try:
        return _Section(text, accessory=thumb)
    except Exception:
        log.debug(
            "components_v2_bridge: Section+Thumbnail failed — falling back to plain text",
            exc_info=True,
        )
        return None


def _build_container(
    children: Sequence[Any],
    *,
    colour: Optional[int],
) -> Any | None:
    """
    Instantiate a :class:`discord.ui.Container` with *children* and accent colour.

    """
    if _Container is None:
        return None

    valid = [c for c in children if c is not None]
    if not valid:
        return None

    for kw in (
        {"accent_colour": colour},
        {"accent_color": colour},
        {},
    ):
        try:
            return _Container(*valid, **kw)
        except TypeError:
            continue

    log.warning("components_v2_bridge: Container — all signatures failed")
    return None


def _build_layout_view(items: List[Any]) -> Any | None:
    """Wrap *items* in a :class:`discord.ui.LayoutView`."""
    if _LayoutView is None or not items:
        return None
    try:
        layout = _LayoutView()
        for item in items:
            layout.add_item(item)
        return layout
    except Exception:
        log.exception("components_v2_bridge: failed to build LayoutView")
        return None


# ---------------------------------------------------------------------------
# v1 View migration
# ---------------------------------------------------------------------------

def _extract_action_rows(v1_view: Any) -> List[Any]:
    """
    Extract items from a classic :class:`discord.ui.View` and return them
    wrapped in :class:`discord.ui.ActionRow` instances, grouped by row index.

    Returns an empty list when ActionRow is unavailable or the view has no
    children — the caller logs and continues without them.
    """
    if _ActionRow is None:
        log.debug("components_v2_bridge: ActionRow unavailable, cannot migrate v1 view")
        return []

    children = getattr(v1_view, "_children", None) or getattr(v1_view, "children", None)
    if not children:
        return []

    # Group by row index (0-4), preserving insertion order within each row.
    rows: dict[int, List[Any]] = {}
    for item in children:
        row_idx = getattr(item, "row", 0) or 0
        rows.setdefault(row_idx, []).append(item)

    action_rows: List[Any] = []
    for row_idx in sorted(rows):
        items_in_row = rows[row_idx]
        # Build rows via add_item() so migrated children get proper parent/view
        # wiring for Container/LayoutView. This is especially important for selects.
        current_row: Any | None = None
        for item in items_in_row:
            if current_row is None:
                try:
                    current_row = _ActionRow()
                except Exception:
                    current_row = None

            if current_row is not None:
                try:
                    current_row.add_item(item)
                    continue
                except (TypeError, ValueError):
                    # Row full / incompatible: commit current row and start new one.
                    if getattr(current_row, "children", None):
                        action_rows.append(current_row)
                    try:
                        current_row = _ActionRow()
                        current_row.add_item(item)
                        continue
                    except Exception:
                        current_row = None

            # Constructor fallback for unknown forks/signatures.
            built = None
            for args, kw in (
                ((item,), {}),
                ((), {"components": [item]}),
                ((), {"children": [item]}),
            ):
                try:
                    built = _ActionRow(*args, **kw)
                    break
                except TypeError:
                    continue
            if built is not None:
                action_rows.append(built)
            else:
                log.warning(
                    "components_v2_bridge: ActionRow row %d item %s could not be migrated",
                    row_idx,
                    item.__class__.__name__,
                )

        if current_row is not None and getattr(current_row, "children", None):
            action_rows.append(current_row)

    return action_rows


# ---------------------------------------------------------------------------
# Core transform
# ---------------------------------------------------------------------------

def _build_embed_container(
    embed: discord.Embed,
    prepend_content: str,
    action_rows: List[Any],
) -> Any | None:
    """
    Convert one :class:`discord.Embed` into a V2 :class:`discord.ui.Container`.

    Build order (failures in any optional step are isolated and logged, never
    propagated — the container is always attempted even if images fail):

        1. **Section** + ``Thumbnail`` accessory when ``embed.thumbnail`` is set
           (title / description / fields / footer as one text block); else a
           single **TextDisplay** for that markdown.  ``embed.footer`` text is
           rendered; footer ``icon_url`` is ignored for display.
        2. **MediaGallery** — ``embed.image`` (appended after the text block).
        3. **ActionRow** — migrated buttons / selects from a classic v1 view.
    """
    md = _embed_to_markdown(embed)
    if prepend_content:
        md = f"{prepend_content}\n\n{md}" if md.strip() else prepend_content

    children: List[Any] = []

    thumbnail_url = _embed_image_url(embed, "thumbnail")
    primary: Any | None = None
    if thumbnail_url:
        primary = _build_section_with_thumbnail(md, thumbnail_url)
    if primary is None:
        text = _build_text_display(md)
        if text is not None:
            primary = text
    if primary is not None:
        children.append(primary)

    # embed.image → MediaGallery (isolated: failure drops the image, not the container)
    image_url = _embed_image_url(embed, "image")
    if image_url:
        try:
            gallery = _build_media_gallery(image_url)
            if gallery is not None:
                children.append(gallery)
        except Exception:
            log.warning(
                "components_v2_bridge: MediaGallery construction raised unexpectedly "
                "for %s — image will be dropped", image_url, exc_info=True,
            )

    children.extend(action_rows)

    return _build_container(children, colour=_embed_colour(embed))


def _transform_kwargs(kwargs: dict) -> bool:
    """
    Mutate *kwargs* in-place to use Components V2.

    Returns ``True`` if a V2 transform was applied, ``False`` if the original
    kwargs are left untouched (e.g. no embeds, V2 classes unavailable).

    ``view=`` handling:
    - Absent / MISSING   → build a fresh LayoutView.
    - LayoutView         → append new containers to the existing layout.
    - Classic v1 View    → extract its items into ActionRows, embed them inside
                           the first embed's Container, replace view= entirely.
    """
    embeds = _peek_embeds(kwargs)
    if not embeds:
        return False

    if _LayoutView is None or _Container is None or _TextDisplay is None:
        log.debug("components_v2_bridge: V2 UI classes not available, keeping embeds")
        return False

    existing_view = _unwrap(kwargs.get("view"))
    is_layout_view = existing_view is not None and isinstance(existing_view, _LayoutView)
    is_v1_view = (
        existing_view is not None
        and not is_layout_view
        and isinstance(existing_view, discord.ui.View)
    )

    # Fold message content into the first embed's text to satisfy the V2
    # constraint that content= and component layouts cannot coexist.
    raw_content = _unwrap(kwargs.get("content"), default="")
    if not isinstance(raw_content, str):
        raw_content = str(raw_content) if raw_content else ""

    # Migrate v1 view items — these go *inside* the first embed's Container.
    action_rows: List[Any] = []
    if is_v1_view:
        action_rows = _extract_action_rows(existing_view)
        if not action_rows:
            log.debug(
                "components_v2_bridge: v1 view migration produced no ActionRows — "
                "buttons/selects will be dropped"
            )

    # Build one Container per embed.  Action rows are injected only into the
    # first container so they stay visually associated with that embed.
    containers: List[Any] = []
    for i, embed in enumerate(embeds):
        prepend = raw_content if i == 0 else ""
        rows_for_embed = action_rows if i == 0 else []
        container = _build_embed_container(embed, prepend, rows_for_embed)
        if container is not None:
            containers.append(container)

    if not containers:
        log.warning("components_v2_bridge: no containers built, falling back to embeds")
        return False

    # --- Commit: mutate kwargs only after all builders have succeeded ---
    _pop_embeds(kwargs)
    if raw_content:
        kwargs.pop("content", None)
    if is_v1_view:
        kwargs.pop("view", None)

    if is_layout_view:
        for c in containers:
            existing_view.add_item(c)
        kwargs["view"] = existing_view
    else:
        layout = _build_layout_view(containers)
        if layout is None:
            log.warning("components_v2_bridge: LayoutView construction failed, falling back")
            return False
        kwargs["view"] = layout

    return True


# ---------------------------------------------------------------------------
# Method patching
# ---------------------------------------------------------------------------

def _patch_async_method(target: Any, method_name: str) -> None:
    global _ORIGINAL_INTERACTION_RESPONSE_SEND_MESSAGE, _ORIGINAL_MESSAGE_EDIT

    original = getattr(target, method_name, None)
    if original is None:
        log.debug("components_v2_bridge: %s.%s not found, skipping", target, method_name)
        return

    if getattr(original, "_cv2_patched", False):
        log.debug("components_v2_bridge: %s.%s already patched, skipping", target, method_name)
        return

    if target is discord.InteractionResponse and method_name == "send_message":
        _ORIGINAL_INTERACTION_RESPONSE_SEND_MESSAGE = original
    elif target is discord.Message and method_name == "edit":
        _ORIGINAL_MESSAGE_EDIT = original

    async def wrapped(*args, **kwargs):
        if kwargs.pop(SKIP_COMPONENTS_V2_BRIDGE, False):
            return await original(*args, **kwargs)

        pristine = dict(kwargs)
        transformed = _transform_kwargs(kwargs)
        # Interaction UPDATE with LayoutView must clear legacy fields; if embed /
        # content are left as MISSING, Discord may keep old embeds alongside new
        # components (broken layout or an apparent "second" message block).
        if transformed and method_name == "edit_message" and target is discord.InteractionResponse:
            kwargs["embed"] = None
            if "content" not in kwargs:
                kwargs["content"] = None
        try:
            return await original(*args, **kwargs)
        except discord.HTTPException as exc:
            if transformed:
                # A message that was sent via this bridge has ``components_v2`` set.
                # Discord forbids classic ``embed`` / ``embeds`` on that message;
                # retrying with *pristine* kwargs is invalid and can glitch the client.
                if method_name == "edit_message" and target is discord.InteractionResponse:
                    log.warning(
                        "components_v2_bridge: InteractionResponse.edit_message failed "
                        "(%s); not retrying with classic embeds on a V2-flagged message",
                        exc.status,
                    )
                    raise
                log.debug(
                    "components_v2_bridge: HTTPException on V2 payload (%s), retrying with embeds",
                    exc.status,
                )
                return await original(*args, **pristine)
            raise

    wrapped._cv2_patched = True  # type: ignore[attr-defined]
    setattr(target, method_name, wrapped)
    log.debug("components_v2_bridge: patched %s.%s", target.__name__, method_name)


async def interaction_send_message_without_cv2_bridge(
    response: discord.InteractionResponse,
    **kwargs: Any,
) -> Any:
    """
    Run :meth:`discord.InteractionResponse.send_message` without the embed→LayoutView
    bridge. Prefer this over ``SKIP_COMPONENTS_V2_BRIDGE`` when you need a guarantee
    the hook never runs (e.g. another layer strips unknown kwargs).
    """
    fn = _ORIGINAL_INTERACTION_RESPONSE_SEND_MESSAGE
    if fn is None:
        return await response.send_message(**kwargs)
    return await fn(response, **kwargs)


async def message_edit_without_cv2_bridge(message: discord.Message, **kwargs: Any) -> Any:
    """
    Run :meth:`discord.Message.edit` without the embed→LayoutView bridge.
    Component interactions expose a plain :class:`discord.Message` whose ``edit``
    is patched; use this after ``defer()`` to replace the message in-channel.
    """
    fn = _ORIGINAL_MESSAGE_EDIT
    if fn is None:
        return await message.edit(**kwargs)
    return await fn(message, **kwargs)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def enable_components_v2_embed_bridge() -> None:
    """
    Install the Components V2 embed bridge.

    Idempotent — safe to call multiple times; only the first call has any effect.
    Call this once at bot startup **before** loading cogs.
    """
    global _PATCHED, _LayoutView, _Container, _TextDisplay, _Section
    global _MediaGallery, _MediaGalleryItem, _Thumbnail, _UnfurledMediaItem
    global _ActionRow, _MISSING

    if _PATCHED:
        return

    _LayoutView        = getattr(discord.ui, "LayoutView",        None)
    _Container         = getattr(discord.ui, "Container",         None)
    _TextDisplay       = getattr(discord.ui, "TextDisplay",       None)
    _Section           = getattr(discord.ui, "Section",           None)
    _MediaGallery      = getattr(discord.ui, "MediaGallery",      None)
    # MediaGalleryItem / UnfurledMediaItem live in discord.components and are
    # re-exported on discord; discord.ui does not expose MediaGalleryItem.
    _MediaGalleryItem  = getattr(discord, "MediaGalleryItem", None) or getattr(
        discord.components, "MediaGalleryItem", None
    )
    _Thumbnail         = getattr(discord.ui, "Thumbnail",         None)
    _UnfurledMediaItem = getattr(discord, "UnfurledMediaItem", None) or getattr(
        discord.components, "UnfurledMediaItem", None
    )
    _ActionRow         = getattr(discord.ui, "ActionRow",         None)
    _MISSING           = getattr(discord.utils, "MISSING",        None)

    # Core classes — without these the bridge can't function at all.
    critical = [
        name for name, cls in (
            ("LayoutView",  _LayoutView),
            ("Container",   _Container),
            ("TextDisplay", _TextDisplay),
        )
        if cls is None
    ]
    # Optional classes — degrade gracefully when absent.
    optional_missing = [
        name for name, cls in (
            ("Section",           _Section),
            ("MediaGallery",      _MediaGallery),
            ("MediaGalleryItem",  _MediaGalleryItem),
            ("Thumbnail",        _Thumbnail),
            ("ActionRow",        _ActionRow),
            ("UnfurledMediaItem", _UnfurledMediaItem),
        )
        if cls is None
    ]

    if critical:
        log.warning(
            "components_v2_bridge: critical classes missing (%s) — "
            "bridge inactive, all sends fall back to classic embeds. "
            "Upgrade discord.py to >= 2.5.",
            ", ".join(critical),
        )
    if optional_missing:
        log.info(
            "components_v2_bridge: optional classes missing (%s) — "
            "images and/or buttons may not render in V2 layout.",
            ", ".join(optional_missing),
        )

    _patch_async_method(discord.abc.Messageable,      "send")
    _patch_async_method(discord.InteractionResponse,  "send_message")
    _patch_async_method(discord.InteractionResponse,  "edit_message")
    _patch_async_method(discord.Webhook,              "send")
    _patch_async_method(discord.WebhookMessage,       "edit")
    _patch_async_method(discord.Message,              "edit")

    _PATCHED = True
    log.info("components_v2_bridge: installed on 6 methods")