#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# PatchBay Canvas engine using QGraphicsView/Scene
# Copyright (C) 2010-2019 Filipe Coelho <falktx@falktx.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of
# the License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# For a full copy of the GNU General Public License see the doc/GPL.txt file.

# ------------------------------------------------------------------------------------------------------------
# Imports (Global)

import os

from PyQt5.QtCore import qCritical, QRectF, QFile
from PyQt5.QtGui import QPainter, QPalette, QIcon, QPixmap
from PyQt5.QtSvg import QGraphicsSvgItem, QSvgRenderer
from PyQt5.QtWidgets import QGraphicsColorizeEffect, QGraphicsPixmapItem

# ------------------------------------------------------------------------------------------------------------
# Imports (Custom)

from . import (
    canvas,
    icon2str,
    CanvasIconType,
    ICON_APPLICATION,
    ICON_HARDWARE,
    ICON_DISTRHO,
    ICON_FILE,
    ICON_PLUGIN,
    ICON_LADISH_ROOM,
    ICON_CLIENT,
    ICON_INTERNAL,
    PORT_MODE_INPUT,
    PORT_MODE_OUTPUT
)

# ------------------------------------------------------------------------------------------------------------
def getAppIcon(icon_name):
    #dark = bool(
        #widget.palette().brush(
            #2, QPalette.WindowText).color().lightness() > 128)

    icon = QIcon.fromTheme(icon_name)

    if icon.isNull():
        for ext in ('svg', 'svgz', 'png'):
            filename = ":app_icons/%s.%s" % (icon_name, ext)
            #darkname = ":app_icons/dark/%s.%s" % (icon_name, ext)

            #if dark and QFile.exists(darkname):
                #filename = darkname

            if QFile.exists(filename):
                del icon
                icon = QIcon()
                icon.addFile(filename)
                break

    if icon.isNull():
        for path in ('/usr/local', '/usr', '%s/.local' % os.getenv('HOME')):
            for ext in ('png', 'svg', 'svgz', 'xpm'):
                filename = "%s/share/pixmaps/%s.%s" % (path, icon_name, ext)
                if QFile.exists(filename):
                    del icon
                    icon = QIcon()
                    icon.addFile(filename)
                    break

    return icon

class CanvasIconPixmap(QGraphicsPixmapItem):
    def __init__(self, icon_type, icon_name, parent):
        QGraphicsPixmapItem.__init__(self)
        self.setParentItem(parent)

        self.p_size = QRectF(0.0, 0.0, 24.0, 24.0)
        self.icon = None
        self.x_offset = 4
        self.y_offset = 4

        if icon_type in (ICON_CLIENT, ICON_APPLICATION):
            self.setIcon(icon_type, icon_name)

    def setIcon(self, icon, name):
        self.icon = getAppIcon(name)
        if not self.icon.isNull():
            pixmap = self.icon.pixmap(24, 24)
            self.setPixmap(pixmap)
            self.setOffset(4.0, 4.0)

    def update_zoom(self, scale: float):
        if self.icon is None or scale <= 0.0:
            return

        pixmap = self.icon.pixmap(int(0.5 + 24 * scale), int(0.5 + 24 * scale))
        self.setPixmap(pixmap)
        self.setScale(1.0 / scale)
        self.setOffset(float(self.x_offset * scale), float(self.y_offset * scale))

    def is_null(self)->bool:
        if self.icon is None:
            return True

        return self.icon.isNull()

    def align_at(self, x_pos: int):
        self.x_offset = x_pos
        self.setOffset(float(self.x_offset), self.y_offset)

    def align_right(self, width: int):
        self.x_offset = width - 28
        self.setOffset(float(self.x_offset), self.y_offset)
        
    def type(self):
        return CanvasIconType


class CanvasSvgIcon(QGraphicsSvgItem):
    def __init__(self, icon_type, name, port_mode, parent):
        QGraphicsSvgItem.__init__(self)
        self.setParentItem(parent)

        self.m_renderer = None
        self.p_size = QRectF(4, 4, 24, 24)

        self.m_colorFX = QGraphicsColorizeEffect(self)
        self.m_colorFX.setColor(canvas.theme.box_text.color())

        #self.setGraphicsEffect(self.m_colorFX)
        self.setIcon(icon_type, name, port_mode)

    def setIcon(self, icon, name, port_mode):
        name = name.lower()
        icon_path = ""

        if icon == ICON_APPLICATION:
            self.p_size = QRectF(3, 2, 19, 18)

            if "audacious" in name:
                icon_path = ":/scalable/pb_audacious.svg"
                self.p_size = QRectF(5, 4, 16, 16)
            elif "clementine" in name:
                icon_path = ":/scalable/pb_clementine.svg"
                self.p_size = QRectF(5, 4, 16, 16)
            elif "distrho" in name:
                icon_path = ":/scalable/pb_distrho.svg"
                self.p_size = QRectF(5, 4, 16, 16)
            elif "jamin" in name:
                icon_path = ":/scalable/pb_jamin.svg"
                self.p_size = QRectF(5, 3, 16, 16)
            elif "mplayer" in name:
                icon_path = ":/scalable/pb_mplayer.svg"
                self.p_size = QRectF(5, 4, 16, 16)
            elif "vlc" in name:
                icon_path = ":/scalable/pb_vlc.svg"
                self.p_size = QRectF(5, 3, 16, 16)

            else:
                icon_path = ":/scalable/pb_generic.svg"
                self.p_size = QRectF(4, 4, 24, 24)

        elif icon == ICON_HARDWARE:
            if name == "a2j":
                icon_path = ":/scalable/DIN-5.svg"
                self.p_size = QRectF(4, 4, 24, 24)
            else:
                if port_mode & PORT_MODE_INPUT:
                    icon_path = ":/scalable/audio-headphones.svg"
                elif port_mode & PORT_MODE_OUTPUT:
                    icon_path = ":/scalable/microphone.svg"
                else:
                    icon_path = ":/scalable/pb_hardware.svg"
                self.p_size = QRectF(4, 4, 24, 24)

        elif icon == ICON_DISTRHO:
            icon_path = ":/scalable/pb_distrho.svg"
            self.p_size = QRectF(5, 4, 16, 16)

        elif icon == ICON_FILE:
            icon_path = ":/scalable/pb_file.svg"
            self.p_size = QRectF(5, 4, 16, 16)

        elif icon == ICON_PLUGIN:
            icon_path = ":/scalable/pb_plugin.svg"
            self.p_size = QRectF(5, 4, 16, 16)

        elif icon == ICON_LADISH_ROOM:
            # TODO - make a unique ladish-room icon
            icon_path = ":/scalable/pb_hardware.svg"
            self.p_size = QRectF(5, 2, 16, 16)

        elif icon == ICON_INTERNAL:
            icon_path = ":/scalable/" + name
            self.p_size = QRectF(4, 4, 24, 24)

        else:
            self.p_size = QRectF(0, 0, 0, 0)
            qCritical("PatchCanvas::CanvasIcon.setIcon(%s, %s) - unsupported icon requested" % (
                      icon2str(icon), name.encode()))
            return

        self.m_renderer = QSvgRenderer(icon_path, canvas.scene)
        self.setSharedRenderer(self.m_renderer)
        self.update()

    def update_zoom(self, scale: float):
        pass

    def type(self):
        return CanvasIconType

    def is_null(self)->bool:
        return False

    def align_at(self, x_pos: int):
        self.p_size = QRectF(x_pos, 4, 24, 24)

    def align_right(self, width: int):
        self.p_size = QRectF(width - 28, 4, 24, 24)

    def boundingRect(self):
        return self.p_size

    def paint(self, painter, option, widget):
        if not self.m_renderer:
            QGraphicsSvgItem.paint(self, painter, option, widget)
            return

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.setRenderHint(QPainter.TextAntialiasing, False)
        self.m_renderer.render(painter, self.p_size)
        painter.restore()

# ------------------------------------------------------------------------------------------------------------



