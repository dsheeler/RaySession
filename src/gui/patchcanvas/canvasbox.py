
import sys

from sip import voidptr
from struct import pack
import time

from PyQt5.QtCore import qCritical, Qt, QPoint, QPointF, QRectF, QTimer
from PyQt5.QtGui import (QCursor, QFont, QFontMetrics, QImage,
                         QLinearGradient, QPainter, QPen, QPolygonF,
                         QColor, QIcon, QPixmap, QPainterPath)
from PyQt5.QtWidgets import QGraphicsItem, QMenu, QApplication

# ------------------------------------------------------------------------------------------------------------
# Imports (Custom)

from . import (
    canvas,
    features,
    options,
    CanvasBoxType,
    ACTION_PLUGIN_EDIT,
    ACTION_PLUGIN_SHOW_UI,
    ACTION_PLUGIN_CLONE,
    ACTION_PLUGIN_REMOVE,
    ACTION_PLUGIN_RENAME,
    ACTION_PLUGIN_REPLACE,
    ACTION_GROUP_INFO,
    ACTION_GROUP_JOIN,
    ACTION_GROUP_SPLIT,
    ACTION_GROUP_RENAME,
    ACTION_GROUP_MOVE,
    ACTION_GROUP_WRAP,
    ACTION_PORTS_DISCONNECT,
    ACTION_INLINE_DISPLAY,
    ACTION_CLIENT_SHOW_GUI,
    PORT_MODE_NULL,
    PORT_MODE_INPUT,
    PORT_MODE_OUTPUT,
    PORT_TYPE_NULL,
    PORT_TYPE_AUDIO_JACK,
    PORT_TYPE_MIDI_ALSA,
    PORT_TYPE_MIDI_JACK,
    PORT_TYPE_PARAMETER,
    MAX_PLUGIN_ID_ALLOWED,
    ICON_HARDWARE,
    ICON_INTERNAL,
    ICON_CLIENT,
    DIRECTION_DOWN
)
import patchcanvas.utils as utils
from .canvasboxshadow import CanvasBoxShadow
from .canvasicon import CanvasSvgIcon, CanvasIconPixmap
from .canvasport import CanvasPort
from .canvasportgroup import CanvasPortGroup
from .theme import Theme

from .canvasbox_abstract import (
    CanvasBoxAbstract,
    UNWRAP_BUTTON_NONE,
    UNWRAP_BUTTON_LEFT,
    UNWRAP_BUTTON_CENTER,
    UNWRAP_BUTTON_RIGHT,
    COLUMNS_AUTO,
    COLUMNS_ONE,
    COLUMNS_TWO)

_translate = QApplication.translate


class CanvasBox(CanvasBoxAbstract):
    def __init__(self, group_id: int, group_name: str, icon_type: int,
                 icon_name: str, parent=None):
        CanvasBoxAbstract.__init__(
            self, group_id, group_name, icon_type, icon_name, parent)
    
    def _should_align_port_types(self, port_types: list) -> bool:
        ''' check if we can align port types
            eg, align first midi input to first midi output '''
        align_port_types = True
        port_types_aligner = []
            
        for port_type in port_types:
            aligner_item = []
            for alternate in (False, True):
                n_ins = 0
                n_outs = 0

                for port in canvas.port_list:
                    if (port.group_id != self._group_id
                            or port.port_id not in self._port_list_ids):
                        continue

                    if (port.port_type == port_type
                            and port.is_alternate == alternate):
                        if port.port_mode == PORT_MODE_INPUT:
                            n_ins += 1
                        elif port.port_mode == PORT_MODE_OUTPUT:
                            n_outs += 1

                port_types_aligner.append((n_ins, n_outs))

        winner = PORT_MODE_NULL

        for n_ins, n_outs in port_types_aligner:
            if ((winner == PORT_MODE_INPUT and n_outs > n_ins)
                    or (winner == PORT_MODE_OUTPUT and n_ins > n_outs)):
                align_port_types = False
                break

            if n_ins > n_outs:
                winner = PORT_MODE_INPUT
            elif n_outs > n_ins:
                winner = PORT_MODE_OUTPUT
        
        return align_port_types
    
    def _set_ports_witdhs(
            self, port_types: list, align_port_types: bool) -> dict:
        max_in_width = max_out_width = 0
        last_in_pos = last_out_pos = last_inout_pos = 0
        final_last_in_pos = final_last_out_pos = last_in_pos
        #wrapped_port_pos = self._default_header_height
        
        box_theme = self.get_theme()
        port_spacing = box_theme.port_spacing()
        port_offset = box_theme.port_offset()
        port_type_spacing = box_theme.port_type_spacing()
        last_in_type = last_out_type = PORT_TYPE_NULL
        last_in_alter = last_out_alter = False
        last_port_mode = PORT_MODE_NULL
        
        for port_type in port_types:
            for alternate in (False, True):
                for port in canvas.port_list:
                    if (port.group_id != self._group_id
                            or port.port_id not in self._port_list_ids
                            or port.port_type != port_type
                            or port.is_alternate != alternate):
                        continue

                    port_pos, pg_len = utils.get_portgroup_position(
                        self._group_id, port.port_id, port.portgrp_id)
                    first_of_portgrp = bool(port_pos == 0)
                    last_of_portgrp = bool(port_pos + 1 == pg_len)
                    size = 0
                    max_pwidth = options.max_port_width

                    if port.portgrp_id:
                        for portgrp in canvas.portgrp_list:
                            if not (portgrp.group_id == self._group_id
                                    and portgrp.portgrp_id == port.portgrp_id):
                                continue
                            
                            if port.port_id == portgrp.port_id_list[0]:
                                portgrp_name = utils.get_portgroup_name(
                                    self._group_id, portgrp.port_id_list)

                                if portgrp_name:
                                    portgrp.widget.set_print_name(
                                        portgrp_name,
                                        max_pwidth - canvas.theme.port_grouped_width - 5)
                                else:
                                    portgrp.widget.set_print_name('', 0)
                            
                            port.widget.set_print_name(
                                utils.get_port_print_name(
                                    self._group_id, port.port_id, port.portgrp_id),
                                int(max_pwidth/2))

                            if (portgrp.widget.get_text_width() + 5
                                    > max_pwidth - port.widget.get_text_width()):
                                portgrp.widget.reduce_print_name(
                                    max_pwidth - port.widget.get_text_width() - 5)

                            size = portgrp.widget.get_text_width() \
                                   + max(port.widget.get_text_width() + 6,
                                         canvas.theme.port_grouped_width) \
                                   + port_offset
                            break
                    else:
                        port.widget.set_print_name(port.port_name, max_pwidth)
                        size = max(port.widget.get_text_width() + port_offset, 20)
                    
                    if port.port_mode == PORT_MODE_INPUT:
                        max_in_width = max(max_in_width, size)
                        if (port.port_type != last_in_type
                                or port.is_alternate != last_in_alter):
                            if last_in_type != PORT_TYPE_NULL:
                                last_in_pos += port_type_spacing
                                last_inout_pos += port_type_spacing
                            last_in_type = port.port_type
                            last_in_alter = port.is_alternate

                        last_in_pos += canvas.theme.port_height
                        if last_of_portgrp:
                            last_in_pos += port_spacing

                    elif port.port_mode == PORT_MODE_OUTPUT:
                        max_out_width = max(max_out_width, size)
                        if (port.port_type != last_out_type
                                or port.is_alternate != last_out_alter):
                            if last_out_type != PORT_TYPE_NULL:
                                last_out_pos += port_type_spacing
                                last_inout_pos += port_type_spacing
                            last_out_type = port.port_type
                            last_out_alter = port.is_alternate
                        
                        last_out_pos += canvas.theme.port_height
                        if last_of_portgrp:
                            last_out_pos += port_spacing
                    
                    last_port_mode = port.port_mode
                    last_inout_pos += canvas.theme.port_height
                    if last_of_portgrp:
                        last_inout_pos += port_spacing
                    
                    final_last_in_pos = last_in_pos
                    final_last_out_pos = last_out_pos
                
                if align_port_types:
                    # align port types horizontally
                    if last_in_pos > last_out_pos:
                        last_out_type = last_in_type
                        last_out_alter = last_in_alter
                    else:
                        last_in_type = last_out_type
                        last_in_alter = last_out_alter
                    last_in_pos = last_out_pos = max(last_in_pos, last_out_pos)
        
        return {'last_in_pos': final_last_in_pos,
                'last_out_pos': final_last_out_pos,
                'last_inout_pos': last_inout_pos,
                'max_in_width': max_in_width,
                'max_out_width': max_out_width,
                'last_port_mode': last_port_mode}

    def _set_ports_y_positions(
            self, port_types: list, align_port_types: bool, start_pos: int,
            one_column: bool) -> dict:
        def set_widget_pos(widget, pos):
            if self._wrapping:
                widget.setY(pos - ((pos - wrapped_port_pos)
                                   * self._wrapping_ratio))
            elif self._unwrapping:
                widget.setY(wrapped_port_pos + ((pos - wrapped_port_pos)
                                                * self._wrapping_ratio))
            elif self._wrapped:
                widget.setY(wrapped_port_pos)
            else:
                widget.setY(pos)
            
        ''' ports Y positioning, and get width informations '''
        max_in_width = max_out_width = 0
        last_in_pos = last_out_pos = start_pos
        final_last_in_pos = final_last_out_pos = last_in_pos
        wrapped_port_pos = start_pos
        
        box_theme = self.get_theme()
        port_spacing = box_theme.port_spacing()
        port_type_spacing = box_theme.port_type_spacing()
        last_in_type = last_out_type = PORT_TYPE_NULL
        last_in_alter = last_out_alter = False
        input_segments = []
        output_segments = []
        in_segment = [last_in_pos, last_in_pos]
        out_segment = [last_out_pos, last_out_pos]
        
        for port_type in port_types:
            for alternate in (False, True):
                for port in canvas.port_list:
                    if (port.group_id != self._group_id
                            or port.port_id not in self._port_list_ids
                            or port.port_type != port_type
                            or port.is_alternate != alternate):
                        continue
                    
                    if one_column:
                        last_in_pos = last_out_pos = max(last_in_pos, last_out_pos)
                    
                    port_pos, pg_len = utils.get_portgroup_position(
                        self._group_id, port.port_id, port.portgrp_id)
                    first_of_portgrp = bool(port_pos == 0)
                    if port.portgrp_id and not first_of_portgrp:
                        continue

                    if port.port_mode == PORT_MODE_INPUT:
                        if (port.port_type != last_in_type
                                or port.is_alternate != last_in_alter):
                            if last_in_type != PORT_TYPE_NULL:
                                last_in_pos += port_type_spacing
                            last_in_type = port.port_type
                            last_in_alter = port.is_alternate
                        
                        if last_in_pos >= in_segment[1] + port_spacing + port_type_spacing:
                            if in_segment[0] != in_segment[1]:
                                input_segments.append(in_segment)
                            in_segment = [last_in_pos, last_in_pos]
                        
                        if port.portgrp_id:
                            # we place the portgroup widget and all its ports now
                            # because in one column mode, we can't be sure
                            # that port consecutivity isn't break by a port with
                            # another mode:
                            # 
                            # input L
                            #     output L
                            # input R
                            #     output R 
                            for portgrp in canvas.portgrp_list:
                                if (portgrp.group_id == self._group_id
                                        and portgrp.portgrp_id == port.portgrp_id):
                                    if portgrp.widget is not None:
                                        set_widget_pos(portgrp.widget, last_in_pos)
                                
                                    for port_id in portgrp.port_id_list:
                                        for gp_port in canvas.port_list:
                                            if (gp_port.group_id == self._group_id
                                                    and gp_port.port_id == port_id):
                                                set_widget_pos(gp_port.widget, last_in_pos)
                                                last_in_pos += canvas.theme.port_height
                                                break
                                    break
                        else:
                            set_widget_pos(port.widget, last_in_pos)
                            last_in_pos += canvas.theme.port_height
                        in_segment[1] = last_in_pos
                        last_in_pos += port_spacing

                    elif port.port_mode == PORT_MODE_OUTPUT:
                        if (port.port_type != last_out_type
                                or port.is_alternate != last_out_alter):
                            if last_out_type != PORT_TYPE_NULL:
                                last_out_pos += port_type_spacing
                            last_out_type = port.port_type
                            last_out_alter = port.is_alternate

                        if last_out_pos >= out_segment[1] + port_spacing + port_type_spacing:
                            if out_segment[0] != out_segment[1]:
                                output_segments.append(out_segment)
                            out_segment = [last_out_pos, last_out_pos]

                        if port.portgrp_id:
                            for portgrp in canvas.portgrp_list:
                                if (portgrp.group_id == self._group_id
                                        and portgrp.portgrp_id == port.portgrp_id):
                                    if portgrp.widget is not None:
                                        set_widget_pos(portgrp.widget, last_out_pos)
                                
                                    for port_id in portgrp.port_id_list:
                                        for gp_port in canvas.port_list:
                                            if (gp_port.group_id == self._group_id
                                                    and gp_port.port_id == port_id):
                                                set_widget_pos(gp_port.widget, last_out_pos)
                                                last_out_pos += canvas.theme.port_height
                                                break
                                    break
                        else:
                            set_widget_pos(port.widget, last_out_pos)
                            last_out_pos += canvas.theme.port_height
                        
                        out_segment[1] = last_out_pos
                        last_out_pos += port_spacing
                
                if align_port_types:
                    # align port types horizontally
                    if last_in_pos > last_out_pos:
                        last_out_type = last_in_type
                        last_out_alter = last_in_alter
                    else:
                        last_in_type = last_out_type
                        last_in_alter = last_out_alter
                    last_in_pos = last_out_pos = max(last_in_pos, last_out_pos)
        
        if in_segment[0] != in_segment[1]:
            input_segments.append(in_segment)
        if out_segment[0] != out_segment[1]:
            output_segments.append(out_segment)
        
        return {'input_segments': input_segments,
                'output_segments': output_segments}
    
    def _choose_title_disposition(
        self, box_height: int, width_for_ports: int,
        box_height_one: int, width_for_ports_one: int) -> dict:
        ''' choose in how many lines should be splitted the title
        returns needed more_height '''

        # Check Text Name size
        title_template = {"title_width": 0, "header_width": 0}
        all_title_templates = [title_template.copy() for i in range(5)]

        for i in range(1, 5):
            max_title_size = 0
            title_lines = self._split_title(i)

            for title_line in title_lines:
                max_title_size = max(max_title_size, title_line.size)

            all_title_templates[i]
            header_width = max_title_size

            if self.has_top_icon():
                header_width += 37
            else:
                header_width += 16

            header_width =  max(200 if self._plugin_inline != self.INLINE_DISPLAY_DISABLED else 50,
                                header_width)

            new_title_template = title_template.copy()
            new_title_template['title_width'] = max_title_size
            new_title_template['header_width'] = header_width
            all_title_templates[i] = new_title_template

            if header_width < width_for_ports_one:
                break

        more_height = 14
        lines_choice_max = i
        one_column = False
        
        sizes_tuples = []
        
        if self._column_disposition in (COLUMNS_AUTO, COLUMNS_ONE):
            sizes_tuples.append(
                (max(all_title_templates[1]['header_width'], width_for_ports_one)
                * box_height_one,
                1, True))
            
            if lines_choice_max >= 2:
                sizes_tuples.append(
                    (max(all_title_templates[2]['header_width'], width_for_ports_one)
                    * box_height_one,
                    2, True))
                
            if lines_choice_max >= 3:
                sizes_tuples.append(
                    (max(all_title_templates[3]['header_width'], width_for_ports_one)
                    * (box_height_one + more_height),
                    3, True))
            
            if lines_choice_max >= 4:
                sizes_tuples.append(
                    (max(all_title_templates[4]['header_width'], width_for_ports_one)
                    * (box_height_one + more_height) + 5000,
                    4, True))

        if self._column_disposition in (COLUMNS_AUTO, COLUMNS_TWO):
            sizes_tuples.append(
                (max(all_title_templates[1]['header_width'], width_for_ports)
                * box_height,
                1, False))
            
            if lines_choice_max >= 2:
                sizes_tuples.append(
                    (max(all_title_templates[2]['header_width'], width_for_ports)
                    * box_height,
                    2, False))
                
            if lines_choice_max >= 3:
                sizes_tuples.append(
                    (max(all_title_templates[3]['header_width'], width_for_ports)
                    * (box_height + more_height),
                    3, False))
            
            if lines_choice_max >= 4:
                sizes_tuples.append(
                    (max(all_title_templates[4]['header_width'], width_for_ports)
                    * (box_height + more_height) + 5000,
                    4, False))
        
        sizes_tuples.sort()
        lines_choice = sizes_tuples[0][1]
        one_column = sizes_tuples[0][2]
        
        self._title_lines = self._split_title(lines_choice)
        
        if lines_choice <= 2:
            more_height = 0
        
        header_width = all_title_templates[lines_choice]['header_width']
        max_title_size = all_title_templates[lines_choice]['title_width']

        return {'max_title_size': max_title_size,
                'header_width': header_width,
                'more_height': more_height,
                'one_column': one_column}
    
    def _push_down_ports(self, down_height: int):
        # down ports
        for port in canvas.port_list:
            if (port.group_id == self._group_id
                    and port.port_id in self._port_list_ids):
                port.widget.setY(port.widget.y() + down_height)

        # down portgroups
        for portgrp in canvas.portgrp_list:
            if (portgrp.group_id == self._group_id
                    and self._current_port_mode & portgrp.port_mode):
                if portgrp.widget is not None:
                    portgrp.widget.setY(portgrp.widget.y() + down_height)
    
    def _set_ports_x_positions(self, max_in_width: int, max_out_width: int):
        box_theme = self.get_theme()
        port_offset = box_theme.port_offset()
        
        # Horizontal ports re-positioning
        inX = port_offset
        outX = self._width - max_out_width - 12

        # Horizontal ports not in portgroup re-positioning
        for port in canvas.port_list:
            if (port.group_id != self._group_id
                    or port.port_id not in self._port_list_ids
                    or port.portgrp_id):
                continue

            if port.port_mode == PORT_MODE_INPUT:
                port.widget.setX(inX)
                port.widget.set_port_width(max_in_width - port_offset)
            elif port.port_mode == PORT_MODE_OUTPUT:
                port.widget.setX(outX)
                port.widget.set_port_width(max_out_width - port_offset)

        # Horizontal portgroups and ports in portgroup re-positioning
        for portgrp in canvas.portgrp_list:
            if (portgrp.group_id != self._group_id
                    or not self._current_port_mode & portgrp.port_mode):
                continue

            if portgrp.widget is not None:
                if portgrp.port_mode == PORT_MODE_INPUT:
                    portgrp.widget.set_portgrp_width(max_in_width - port_offset)
                    portgrp.widget.setX(box_theme.port_offset() +1)
                elif portgrp.port_mode == PORT_MODE_OUTPUT:
                    portgrp.widget.set_portgrp_width(max_out_width - port_offset)
                    portgrp.widget.setX(outX)

            max_port_in_pg_width = canvas.theme.port_grouped_width
            portgrp_name = utils.get_portgroup_name(
                self._group_id, portgrp.port_id_list)

            for port in canvas.port_list:
                if (port.group_id == self._group_id
                        and port.port_id in portgrp.port_id_list
                        and port.widget is not None):
                    port_print_width = port.widget.get_text_width()

                    # change port in portgroup width only if
                    # portgrp will have a name
                    # to ensure that portgroup widget is large enough
                    if portgrp_name:
                        max_port_in_pg_width = max(max_port_in_pg_width,
                                                   port_print_width + 4)

            out_in_portgrpX = (self._width - box_theme.port_offset() - 12
                               - max_port_in_pg_width)

            portgrp.widget.set_ports_width(max_port_in_pg_width)

            for port in canvas.port_list:
                if (port.group_id == self._group_id
                        and port.port_id in portgrp.port_id_list
                        and port.widget is not None):
                    port.widget.set_port_width(max_port_in_pg_width)
                    if port.port_mode == PORT_MODE_INPUT:
                        port.widget.setX(inX)
                    elif port.port_mode == PORT_MODE_OUTPUT:
                        port.widget.setX(out_in_portgrpX)
    
    def build_painter_path(self, pos_dict):
        input_segments = pos_dict['input_segments']
        output_segments = pos_dict['output_segments']
        
        painter_path = QPainterPath()
        theme = self.get_theme()
        border_radius = theme.border_radius()
        port_offset = theme.port_offset()
        pen = theme.fill_pen()
        line_hinting = pen.widthF() / 2.0
        rect = QRectF(0.0, 0.0, self._width, self._height)
        rect.adjust(line_hinting, line_hinting, -line_hinting, -line_hinting)
        
        if border_radius == 0.0:
            painter_path.addRect(rect)
        else:
            painter_path.addRoundedRect(rect, border_radius, border_radius)
        
        if not (self._wrapping or self._unwrapping or self._wrapped):
            if port_offset != 0.0:
                port_offset = abs(port_offset)
                for in_segment in input_segments:
                    moins_path = QPainterPath()
                    moins_path.addRect(
                        QRectF(0.0, in_segment[0] - line_hinting,
                            port_offset + line_hinting, in_segment[1] - in_segment[0] + line_hinting * 2))
                    painter_path = painter_path.subtracted(moins_path)
                    
                for out_segment in output_segments:
                    moins_path = QPainterPath()
                    moins_path.addRect(
                        QRectF(self._width - line_hinting - port_offset, out_segment[0] - line_hinting,
                            port_offset + line_hinting, out_segment[1] - out_segment[0] + line_hinting * 2))
                    painter_path = painter_path.subtracted(moins_path)
            #elif port_offset < 0.0:
                #for in_segment in input_segments:
                    #plus_path = QPainterPath()
                    #plus_path.addRect(
                        #QRectF(port_offset + line_hinting, in_segment[0] - line_hinting,
                            #- port_offset + line_hinting * 2, in_segment[1] - in_segment[0] + line_hinting * 2))
                    #painter_path = painter_path.united(plus_path)
                    
                #for out_segment in output_segments:
                    #plus_path = QPainterPath()
                    #plus_path.addRect(
                        #QRectF(self._width - line_hinting, out_segment[0] - line_hinting,
                            #- port_offset, out_segment[1] - out_segment[0] + line_hinting * 2))
                    #painter_path = painter_path.united(plus_path)

            if (input_segments
                    and self._height - input_segments[-1][1] <= theme.border_radius()):
                down_left_rect = QRectF(0.0 + line_hinting, self._height - 3.5,
                                        3.5, 3.5 - line_hinting)
                left_path = QPainterPath()
                left_path.addRect(down_left_rect)
                painter_path = painter_path.united(left_path)
            
            if (output_segments
                    and self._height - output_segments[-1][1] <= theme.border_radius()):
                down_right_rect = QRectF(
                    self._width - 3.5 - line_hinting, self._height - 3.5,
                    3.5, 3.5 - line_hinting)
                right_path = QPainterPath()
                right_path.addRect(down_right_rect)
                painter_path = painter_path.united(right_path)

        self._painter_path = painter_path
        
    def update_positions(self, even_animated=False):
        if canvas.loading_items:
            return
        
        if (not even_animated
                and self in [b['widget'] for b in canvas.scene.move_boxes]):
            # do not change box disposition while box is moved by animation
            # update_positions will be called when animation is finished
            return

        self.prepareGeometryChange()
        
        self._current_port_mode = PORT_MODE_NULL
        for port in canvas.port_list:
            if port.group_id == self._group_id and port.port_id in self._port_list_ids:
                # used to know present port modes (INPUT or OUTPUT)
                self._current_port_mode |= port.port_mode

        port_types = [PORT_TYPE_AUDIO_JACK, PORT_TYPE_MIDI_JACK,
                      PORT_TYPE_MIDI_ALSA, PORT_TYPE_PARAMETER]
    
        align_port_types = self._should_align_port_types(port_types)

        widths_dict = self._set_ports_witdhs(port_types, align_port_types)
        last_in_pos = widths_dict['last_in_pos'] + self._default_header_height
        last_out_pos = widths_dict['last_out_pos'] + self._default_header_height
        last_inout_pos = widths_dict['last_inout_pos'] + self._default_header_height
        max_in_width = widths_dict['max_in_width']
        max_out_width = widths_dict['max_out_width']
        last_port_mode = widths_dict['last_port_mode']
        
        wrapped_port_pos = self._default_header_height
        
        box_theme = self.get_theme()
        box_height = max(last_in_pos, last_out_pos) + box_theme.box_footer()
        box_height_one = last_inout_pos + box_theme.box_footer()

        width_for_ports = 30
        if self._plugin_inline != self.INLINE_DISPLAY_DISABLED:
            width_for_ports = 100
        
        width_for_ports_one = width_for_ports
        width_for_ports += max_in_width + max_out_width
        width_for_ports_one += max(max_in_width, max_out_width)

        self._width_in = max_in_width
        self._width_out = max_out_width
        
        titles_dict = self._choose_title_disposition(
            box_height, width_for_ports, box_height_one, width_for_ports_one)
        max_title_size = titles_dict['max_title_size']
        more_height = titles_dict['more_height']
        one_column = titles_dict['one_column']
        #one_column = True

        if one_column:
            width_for_ports = width_for_ports_one
            box_height = box_height_one

        self._width = max(titles_dict['header_width'], width_for_ports)
        
        if more_height:
            box_height += more_height
            #self._push_down_ports(more_height)
            last_in_pos += more_height
            last_out_pos += more_height
        
        ports_y_segments_dict = self._set_ports_y_positions(
            port_types, align_port_types,
            self._default_header_height + more_height,
            one_column)
        self._set_ports_x_positions(max_in_width, max_out_width)
        
        # wrapped/unwrapped sizes
        normal_height = box_height
        wrapped_height = wrapped_port_pos + canvas.theme.port_height + more_height
        self._header_height = self._default_header_height + more_height

        if self._wrapping:
            self._height = (normal_height
                            - (normal_height - wrapped_height)
                              * self._wrapping_ratio)
        elif self._unwrapping:
            self._height = (wrapped_height
                            + (normal_height - wrapped_height)
                              * self._wrapping_ratio)
        elif self._wrapped:
            self._height = wrapped_height
        else:
            self._height = normal_height
            
            self._unwrap_triangle_pos = UNWRAP_BUTTON_NONE
            if self._height >= 100:
                if one_column and last_port_mode == PORT_MODE_INPUT:
                    self._unwrap_triangle_pos = UNWRAP_BUTTON_RIGHT
                elif one_column and last_port_mode == PORT_MODE_OUTPUT:
                    self._unwrap_triangle_pos = UNWRAP_BUTTON_LEFT
                elif last_out_pos > last_in_pos:
                    self._unwrap_triangle_pos = UNWRAP_BUTTON_LEFT
                elif last_in_pos > last_out_pos:
                    self._unwrap_triangle_pos = UNWRAP_BUTTON_RIGHT
                else:
                    self._unwrap_triangle_pos = UNWRAP_BUTTON_CENTER
        
        down_height = box_theme.fill_pen().widthF()

        self._wrapped_height = wrapped_height + down_height
        self._unwrapped_height = normal_height + down_height
        self._height += down_height

        # round self._height to the upper value
        self._height = float(int(self._height + 0.99))

        if self.has_top_icon():
            self.top_icon.align_at((self._width - max_title_size - 29)/2)
        
        self.build_painter_path(ports_y_segments_dict)
        
        if (self._width != self._ex_width
                or self._height != self._ex_height
                or self.scenePos() != self._ex_scene_pos):
            canvas.scene.resize_the_scene()

        self._ex_width = self._width
        self._ex_height = self._height
        self._ex_scene_pos = self.scenePos()
        
        self.repaint_lines(forced=True)

        if not (self._wrapping or self._unwrapping) and self.isVisible():
            canvas.scene.deplace_boxes_from_repulsers([self])
            
        self.update()
