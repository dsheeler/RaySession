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

from PyQt5.QtCore import qWarning, Qt, QLineF
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtWidgets import QGraphicsLineItem

# ------------------------------------------------------------------------------------------------------------
# Imports (Custom)

from . import (
    canvas,
    options,
    port_mode2str,
    port_type2str,
    CanvasLineMovType,
    CanvasPortType,
    CanvasPortGroupType,
    PORT_MODE_INPUT,
    PORT_MODE_OUTPUT,
    PORT_TYPE_AUDIO_JACK,
    PORT_TYPE_MIDI_ALSA,
    PORT_TYPE_MIDI_JACK,
    PORT_TYPE_PARAMETER,
)

# ------------------------------------------------------------------------------------------------------------

class CanvasLineMov(QGraphicsLineItem):
    def __init__(self, port_mode, port_type, port_pos, portgrp_len, parent):
        QGraphicsLineItem.__init__(self)
        self.setParentItem(parent)

        self.m_port_mode = port_mode
        self.m_port_type = port_type
        self.m_port_pos_from = port_pos
        self.m_port_pos_dest = port_pos
        self.m_portgrp_len_from = portgrp_len
        self.m_portgrp_len_dest = portgrp_len

        # Port position doesn't change while moving around line
        self.p_lineX = self.scenePos().x()
        self.p_lineY = self.scenePos().y()
        self.p_width = parent.getPortWidth()

        if port_type == PORT_TYPE_AUDIO_JACK:
            pen = QPen(canvas.theme.line_audio_jack, 2)
        elif port_type == PORT_TYPE_MIDI_JACK:
            pen = QPen(canvas.theme.line_midi_jack, 2)
        elif port_type == PORT_TYPE_MIDI_ALSA:
            pen = QPen(canvas.theme.line_midi_alsa, 2)
        elif port_type == PORT_TYPE_PARAMETER:
            pen = QPen(canvas.theme.line_parameter, 2)
        else:
            qWarning("PatchCanvas::CanvasLineMov(%s, %s, %s) - invalid port type" % (port_mode2str(port_mode), port_type2str(port_type), parent))
            pen = QPen(Qt.black)

        pen.setCapStyle(Qt.RoundCap)
        pen.setWidthF(pen.widthF() + 0.00001)
        self.setPen(pen)

    def setDestinationPortGroupPosition(self, port_pos, portgrp_len):
        self.m_port_pos_dest = port_pos
        self.m_portgrp_len_dest = portgrp_len

    def updateLinePos(self, scenePos):
        phi = 0.75 if self.m_portgrp_len_from > 2 else 0.62
        phito = 0.75 if self.m_portgrp_len_dest > 2 else 0.62

        item_pos = [0, 0]

        if self.m_port_mode == PORT_MODE_INPUT:
            item_pos[0] = 0
        elif self.m_port_mode == PORT_MODE_OUTPUT:
            item_pos[0] = self.p_width + 12
        else:
            return

        if self.parentItem().type() == CanvasPortType:
            if self.m_portgrp_len_from > 1:
                first_old_y = canvas.theme.port_height * phi
                last_old_y  = canvas.theme.port_height * (self.m_portgrp_len_from - phi)
                delta = (last_old_y - first_old_y) / (self.m_portgrp_len_from -1)
                item_pos[1] = first_old_y + (self.m_port_pos_from * delta) \
                              - (canvas.theme.port_height * self.m_port_pos_from)
            else:
                item_pos[1] = float(canvas.theme.port_height)/2

        elif self.parentItem().type() == CanvasPortGroupType:
            first_old_y = canvas.theme.port_height * phi
            last_old_y  = canvas.theme.port_height * (self.m_portgrp_len_from - phi)
            delta = (last_old_y - first_old_y) / (self.m_portgrp_len_from -1)
            item_pos[1] = first_old_y + (self.m_port_pos_from * delta)

        if self.m_portgrp_len_dest == 1:
            mouse_y_offset = 0
        else:
            first_new_y = canvas.theme.port_height * phito
            last_new_y  = canvas.theme.port_height * (self.m_portgrp_len_dest - phito)
            delta = (last_new_y - first_new_y) / (self.m_portgrp_len_dest -1)
            new_y1 = first_new_y + (self.m_port_pos_dest * delta)
            mouse_y_offset = new_y1 - ( (last_new_y - first_new_y) / 2 ) - (canvas.theme.port_height * phito)

        line = QLineF(item_pos[0], item_pos[1], scenePos.x() - self.p_lineX, scenePos.y() - self.p_lineY + mouse_y_offset)
        self.setLine(line)

    def type(self):
        return CanvasLineMovType

    def paint(self, painter, option, widget):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, bool(options.antialiasing))
        QGraphicsLineItem.paint(self, painter, option, widget)
        painter.restore()

# ------------------------------------------------------------------------------------------------------------
