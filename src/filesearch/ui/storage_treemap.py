"""Treemap widget for storage visualization."""

from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFontMetrics, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QWidget

from filesearch.core.treemap_layout import layout_treemap
from filesearch.models.storage_node import StorageNode, format_bytes
from filesearch.ui.theme import Colors, Spacing


@dataclass(slots=True)
class _VisibleTile:
    """One painted treemap tile."""

    node: StorageNode
    rect: QRectF
    depth: int
    color_index: int
    header_height: float


class StorageTreemapWidget(QWidget):
    """Custom-painted treemap widget."""

    node_hovered = pyqtSignal(object)
    node_activated = pyqtSignal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setMinimumHeight(500)
        self._current_node: StorageNode | None = None
        self._tiles: list[_VisibleTile] = []
        self._hovered_node: StorageNode | None = None
        self._padding = 4.0
        self._inner_padding = 4.0
        self._color_ramp = [
            QColor(Colors.PRIMARY),
            QColor(Colors.TAG_GREEN),
            QColor(Colors.TAG_YELLOW),
            QColor(Colors.TAG_BLUE),
            QColor(Colors.TAG_PURPLE),
        ]

    def clear(self) -> None:
        """Clear all treemap content."""
        self._current_node = None
        self._tiles.clear()
        self._hovered_node = None
        self.node_hovered.emit(None)
        self.update()

    def set_root_node(self, node: StorageNode | None) -> None:
        """Set the currently visible node."""
        self._current_node = node
        self._hovered_node = None
        self._rebuild_layout()
        self.node_hovered.emit(None)
        self.update()

    def resizeEvent(self, event) -> None:
        """Recompute layout on resize."""
        self._rebuild_layout()
        super().resizeEvent(event)

    def leaveEvent(self, event) -> None:
        """Reset hover state when the cursor leaves the widget."""
        self._hovered_node = None
        self.node_hovered.emit(None)
        self.setToolTip("")
        self.update()
        super().leaveEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """Track hovered tiles."""
        node = self._node_at(event.position())
        if node is self._hovered_node:
            super().mouseMoveEvent(event)
            return

        self._hovered_node = node
        self.node_hovered.emit(node)
        if node is not None:
            kind = "Folder" if node.is_dir else "File"
            self.setToolTip(
                f"{node.name}\n{kind}\n{format_bytes(node.size)}\n{node.path}"
            )
        else:
            self.setToolTip("")
        self.update()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event) -> None:
        """Emit activation when a directory tile is clicked."""
        if event.button() == Qt.MouseButton.LeftButton:
            node = self._node_at(event.position())
            if node is not None:
                self.node_activated.emit(node)
                event.accept()
                return
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:
        """Render the treemap tiles."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(Colors.BG_SECONDARY))

        if not self._tiles:
            painter.end()
            return

        metrics = QFontMetrics(self.font())
        for tile in self._tiles:
            node = tile.node
            rect = tile.rect
            if rect.width() <= 1 or rect.height() <= 1:
                continue

            hovered = node == self._hovered_node
            fill_color = self._tile_color(node, tile.color_index, tile.depth)
            fill_color = fill_color.lighter(118 if hovered else 100)
            border_color = QColor(
                Colors.TEXT_PRIMARY if hovered else Colors.BORDER_STRONG
            )

            path = QPainterPath()
            path.addRoundedRect(rect, Spacing.RADIUS_SM, Spacing.RADIUS_SM)
            painter.fillPath(path, fill_color)
            painter.setPen(QPen(border_color, 1.4 if hovered else 1.0))
            painter.drawPath(path)

            if rect.width() < 52 or rect.height() < 28:
                continue

            text_rect = self._label_rect(tile)
            if text_rect.width() <= 0 or text_rect.height() <= 0:
                continue

            name = metrics.elidedText(
                node.name, Qt.TextElideMode.ElideRight, int(text_rect.width())
            )
            size = metrics.elidedText(
                format_bytes(node.size),
                Qt.TextElideMode.ElideRight,
                int(text_rect.width()),
            )

            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextSingleLine,
                name,
            )

            if text_rect.height() >= 32:
                secondary_rect = text_rect.adjusted(0, 18, 0, 0)
                painter.setPen(QColor(255, 255, 255, 190))
                painter.drawText(
                    secondary_rect,
                    Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextSingleLine,
                    size,
                )

        painter.end()

    def _rebuild_layout(self) -> None:
        """Recompute the treemap rectangles from the current node."""
        self._tiles = []
        if self._current_node is None:
            return

        bounds = self.rect().adjusted(8, 8, -8, -8)
        if bounds.width() <= 0 or bounds.height() <= 0:
            return

        self._layout_children(
            self._current_node.children,
            bounds,
            depth=0,
            color_seed=0,
        )

    def _node_at(self, point: QPointF) -> StorageNode | None:
        """Return the node under *point*, if any."""
        for tile in reversed(self._tiles):
            if tile.rect.contains(point):
                return tile.node
        return None

    def _layout_children(
        self,
        children: list[StorageNode],
        bounds: QRectF,
        depth: int,
        color_seed: int,
    ) -> None:
        """Recursively layout nested tiles for *children* inside *bounds*."""
        visible_children = [child for child in children if child.size > 0]
        if not visible_children:
            return

        laid_out = layout_treemap(
            [(child, float(child.size)) for child in visible_children],
            float(bounds.x()),
            float(bounds.y()),
            float(bounds.width()),
            float(bounds.height()),
        )

        for index, treemap_rect in enumerate(laid_out):
            rect = QRectF(
                treemap_rect.x + self._padding,
                treemap_rect.y + self._padding,
                max(0.0, treemap_rect.width - (self._padding * 2)),
                max(0.0, treemap_rect.height - (self._padding * 2)),
            )
            if rect.width() <= 2 or rect.height() <= 2:
                continue

            node = treemap_rect.item
            tile = _VisibleTile(
                node=node,
                rect=rect,
                depth=depth,
                color_index=color_seed + index,
                header_height=self._header_height(node, rect),
            )
            self._tiles.append(tile)

            child_bounds = self._child_bounds(tile)
            if child_bounds is not None:
                self._layout_children(
                    node.children,
                    child_bounds,
                    depth=depth + 1,
                    color_seed=color_seed + index + depth + 1,
                )

    def _header_height(self, node: StorageNode, rect: QRectF) -> float:
        """Return the reserved label strip height for a directory tile."""
        if not node.is_dir or not any(child.size > 0 for child in node.children):
            return 0.0
        if rect.width() < 78 or rect.height() < 54:
            return 0.0
        if rect.height() >= 120:
            return 26.0
        if rect.height() >= 80:
            return 22.0
        return 18.0

    def _child_bounds(self, tile: _VisibleTile) -> QRectF | None:
        """Return the area available for nested children inside *tile*."""
        if (
            not tile.node.is_dir
            or not tile.node.children
            or tile.rect.width() < 74
            or tile.rect.height() < 50
        ):
            return None

        top_padding = max(self._inner_padding, tile.header_height + self._inner_padding)
        child_rect = tile.rect.adjusted(
            self._inner_padding,
            top_padding,
            -self._inner_padding,
            -self._inner_padding,
        )
        if child_rect.width() < 20 or child_rect.height() < 20:
            return None
        return child_rect

    def _label_rect(self, tile: _VisibleTile) -> QRectF:
        """Return the text rectangle for a tile label."""
        if tile.header_height > 0:
            return QRectF(
                tile.rect.x() + 8,
                tile.rect.y() + 6,
                max(0.0, tile.rect.width() - 16),
                max(0.0, tile.header_height - 8),
            )
        return tile.rect.adjusted(8, 6, -8, -6)

    def _tile_color(self, node: StorageNode, index: int, depth: int) -> QColor:
        """Return a tile color derived from the theme palette."""
        base = QColor(self._color_ramp[index % len(self._color_ramp)])
        if depth:
            base = base.darker(min(135, 100 + (depth * 6)))
        if node.is_dir:
            return base.darker(120)
        return base.lighter(105)
