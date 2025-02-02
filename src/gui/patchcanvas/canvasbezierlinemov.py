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

from PyQt5.QtCore import qWarning, Qt, QPointF
from PyQt5.QtGui import QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import QGraphicsPathItem

# ------------------------------------------------------------------------------------------------------------
# Imports (Custom)

from . import (
    canvas,
    options,
    port_mode2str,
    port_type2str,
    CanvasBezierLineMovType,
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

class CanvasBezierLineMov(QGraphicsPathItem):
    def __init__(self, port_mode, port_type,
                 port_posinportgrp, portgrp_lenght, parent):
        QGraphicsPathItem.__init__(self)
        self.setParentItem(parent)

        self.m_port_mode = port_mode
        self.m_port_type = port_type
        self.m_port_posinportgrp = port_posinportgrp
        self.m_port_posinportgrp_to = port_posinportgrp
        self.m_portgrp_lenght = portgrp_lenght
        self.m_portgrp_lenght_to = portgrp_lenght
        self.m_ready_to_disc  = False

        # Port position doesn't change while moving around line
        self.p_itemX = self.scenePos().x()
        self.p_itemY = self.scenePos().y()
        self.p_width = parent.getPortWidth()

        if self.m_port_type not in (PORT_TYPE_AUDIO_JACK, PORT_TYPE_MIDI_JACK,
                                    PORT_TYPE_MIDI_ALSA, PORT_TYPE_PARAMETER):
            qWarning("PatchCanvas::CanvasBezierLineMov(%s, %s, %s) - invalid port type"
                     % (port_mode2str(self.m_port_mode),
                        port_type2str(self.m_port_type),
                        self.parentItem()))

    def setReadyToDisc(self, yesno):
        self.m_ready_to_disc = yesno

    def toggleReadyToDisc(self):
        self.m_ready_to_disc = not bool(self.m_ready_to_disc)

    def setDestinationPortGroupPosition(self, port_pos, portgrp_len):
        self.m_port_posinportgrp_to = port_pos
        self.m_portgrp_lenght_to = portgrp_len

    def updateLinePos(self, scenePos):
        if self.m_ready_to_disc:
            if self.m_port_type == PORT_TYPE_AUDIO_JACK:
                pen = QPen(canvas.theme.line_audio_jack_sel, 2, Qt.DotLine)
            elif self.m_port_type == PORT_TYPE_MIDI_JACK:
                pen = QPen(canvas.theme.line_midi_jack_sel, 2, Qt.DotLine)
            elif self.m_port_type == PORT_TYPE_MIDI_ALSA:
                pen = QPen(canvas.theme.line_midi_alsa_sel, 2, Qt.DotLine)
            elif self.m_port_type == PORT_TYPE_PARAMETER:
                pen = QPen(canvas.theme.line_parameter_sel, 2, Qt.DotLine)
            else:
                pen = QPen(Qt.black)
        else:
            if self.m_port_type == PORT_TYPE_AUDIO_JACK:
                pen = QPen(canvas.theme.line_audio_jack_sel, 2)
            elif self.m_port_type == PORT_TYPE_MIDI_JACK:
                pen = QPen(canvas.theme.line_midi_jack_sel, 2)
            elif self.m_port_type == PORT_TYPE_MIDI_ALSA:
                pen = QPen(canvas.theme.line_midi_alsa_sel, 2)
            elif self.m_port_type == PORT_TYPE_PARAMETER:
                pen = QPen(canvas.theme.line_parameter_sel, 2)
            else:
                pen = QPen(Qt.black)

        pen.setCapStyle(Qt.FlatCap)
        pen.setWidthF(pen.widthF() + 0.00001)
        self.setPen(pen)

        phi = 0.75 if self.m_portgrp_lenght > 2 else 0.62
        phito = 0.75 if self.m_portgrp_lenght_to > 2 else 0.62

        if self.parentItem().type() == CanvasPortType:
            if self.m_portgrp_lenght > 1:
                first_old_y = canvas.theme.port_height * phi
                last_old_y  = canvas.theme.port_height * (self.m_portgrp_lenght - phi)
                delta = (last_old_y - first_old_y) / (self.m_portgrp_lenght -1)
                old_y = first_old_y + (self.m_port_posinportgrp * delta) \
                        - canvas.theme.port_height * self.m_port_posinportgrp
            else:
                old_y = canvas.theme.port_height / 2

            if self.m_portgrp_lenght_to == 1:
                new_y = 0
            else:
                first_new_y = canvas.theme.port_height * phito
                last_new_y  = canvas.theme.port_height * (self.m_portgrp_lenght_to - phito)
                delta = (last_new_y - first_new_y) / (self.m_portgrp_lenght_to -1)
                new_y1 = first_new_y + (self.m_port_posinportgrp_to * delta)
                new_y = new_y1 - ( (last_new_y - first_new_y) / 2 ) \
                        - canvas.theme.port_height * phito

        elif self.parentItem().type() == CanvasPortGroupType:
            first_old_y = canvas.theme.port_height * phi
            last_old_y  = canvas.theme.port_height * (self.m_portgrp_lenght - phi)
            delta = (last_old_y - first_old_y) / (self.m_portgrp_lenght -1)
            old_y = first_old_y + (self.m_port_posinportgrp * delta)

            if self.m_portgrp_lenght_to == 1:
                new_y = 0
            elif (self.m_port_posinportgrp_to == self.m_port_posinportgrp
                    and self.m_portgrp_lenght == self.m_portgrp_lenght_to):
                new_y = old_y - ( (last_old_y - first_old_y) / 2 ) \
                        - (canvas.theme.port_height * phi)
            else:
                first_new_y = canvas.theme.port_height * phito
                last_new_y  = canvas.theme.port_height * (self.m_portgrp_lenght_to - phito)
                delta = (last_new_y - first_new_y) / (self.m_portgrp_lenght_to -1)
                new_y1 = first_new_y + (self.m_port_posinportgrp_to * delta)
                new_y = new_y1 - ( (last_new_y - first_new_y) / 2 ) \
                        - (canvas.theme.port_height * phito)

        final_x = scenePos.x() - self.p_itemX
        final_y = scenePos.y() - self.p_itemY + new_y

        if self.m_port_mode == PORT_MODE_OUTPUT:
            old_x = self.p_width + 12
            mid_x = abs(final_x - old_x) / 2
            new_x1 = old_x + mid_x
            new_x2 = final_x - mid_x

            diffxy = abs(final_y - old_y) - abs(final_x - old_x)
            if diffxy > 0:
                new_x1 += abs(diffxy)
                new_x2 -= abs(diffxy)

        elif self.m_port_mode == PORT_MODE_INPUT:
            old_x = 0
            mid_x = abs(final_x - old_x) / 2
            new_x1 = old_x - mid_x
            new_x2 = final_x + mid_x

            diffxy = abs(final_y - old_y) - abs(final_x - old_x)
            if diffxy > 0:
                new_x1 -= abs(diffxy)
                new_x2 += abs(diffxy)
        else:
            return

        path = QPainterPath(QPointF(old_x, old_y))
        path.cubicTo(new_x1, old_y, new_x2, final_y, final_x, final_y)
        self.setPath(path)

    def type(self):
        return CanvasBezierLineMovType

    def paint(self, painter, option, widget):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, bool(options.antialiasing))
        QGraphicsPathItem.paint(self, painter, option, widget)
        painter.restore()

# ------------------------------------------------------------------------------------------------------------
