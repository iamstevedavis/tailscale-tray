from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPainterPath, QPen, QPixmap


BASE_BG = QColor("#0F5EA8")
BASE_RING = QColor("#0A3F71")
TEXT = QColor("#FFFFFF")
STATUS_COLORS = {
    "connected": QColor("#22C55E"),
    "connecting": QColor("#F59E0B"),
    "warning": QColor("#F97316"),
    "critical": QColor("#DC2626"),
    "stopped": QColor("#6B7280"),
}


def build_tray_icon(icon_key: str, size: int = 64) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    _draw_base_badge(painter, size)
    _draw_letters(painter, size)
    _draw_status_overlay(painter, size, icon_key)

    painter.end()
    return QIcon(pixmap)


def _draw_base_badge(painter: QPainter, size: int) -> None:
    outer = QRectF(2, 2, size - 4, size - 4)
    inner = QRectF(6, 6, size - 12, size - 12)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(BASE_RING))
    painter.drawEllipse(outer)
    painter.setBrush(QBrush(BASE_BG))
    painter.drawEllipse(inner)


def _draw_letters(painter: QPainter, size: int) -> None:
    font = QFont("Sans Serif")
    font.setBold(True)
    font.setPixelSize(int(size * 0.23))
    painter.setFont(font)
    painter.setPen(QPen(TEXT))

    align = Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
    painter.drawText(QRectF(0, size * 0.02, size, size * 0.24), align, "T")
    painter.drawText(QRectF(0, size * 0.62, size, size * 0.20), align, "S")


def _draw_status_overlay(painter: QPainter, size: int, icon_key: str) -> None:
    color = STATUS_COLORS.get(icon_key, STATUS_COLORS["stopped"])
    center = QPointF(size / 2, size / 2)
    radius = size * 0.16

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(color))
    painter.drawEllipse(center, radius, radius)

    pen = QPen(QColor("#FFFFFF"))
    pen.setWidthF(max(2.5, size * 0.05))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    if icon_key == "connected":
        path = QPainterPath()
        path.moveTo(size * 0.40, size * 0.50)
        path.lineTo(size * 0.48, size * 0.58)
        path.lineTo(size * 0.62, size * 0.41)
        painter.drawPath(path)
    elif icon_key == "connecting":
        painter.drawArc(
            QRectF(size * 0.34, size * 0.34, size * 0.32, size * 0.32),
            40 * 16,
            280 * 16,
        )
    elif icon_key == "warning":
        painter.drawLine(QPointF(size * 0.50, size * 0.41), QPointF(size * 0.50, size * 0.54))
        painter.drawPoint(QPointF(size * 0.50, size * 0.60))
    elif icon_key == "critical":
        painter.drawLine(QPointF(size * 0.42, size * 0.42), QPointF(size * 0.58, size * 0.58))
        painter.drawLine(QPointF(size * 0.58, size * 0.42), QPointF(size * 0.42, size * 0.58))
    else:
        painter.drawLine(QPointF(size * 0.42, size * 0.58), QPointF(size * 0.58, size * 0.42))
