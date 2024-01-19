import html
from datetime import datetime
import math
from typing import List, Optional, Tuple

from pydantic.dataclasses import dataclass

@dataclass
class SVGConfig:
    """
    Configuration class for SVG generation.

    Attributes:
        width (int): Width of the SVG canvas in pixels.
        height (int): Height of the SVG canvas in pixels.
        legend_height (int): Height reserved for the legend in pixels.
        font (str): Font family for text elements.
        font_size (int): Font size in points for text elements.
        indent (str): Indentation string, default is two spaces.
        default_color (str): Default color code for SVG elements.
    """
    width: int = 600
    height: int = 600
    legend_height: int = 150
    font: str = "Arial"
    font_size: int = 12
    indent: str = "  "
    default_color: str = "#C0C0C0"

    @property
    def total_height(self) -> int:
        """
        Calculate total height of the SVG canvas including the legend.

        Returns:
            int: Total height of the SVG canvas.
        """
        return self.height + self.legend_height

@dataclass
class SVGNode:
    """
    a generic SVG Node
    """
    indent_level: int = 1
    id: Optional[str] = None
    color: Optional[str] = None   # Color of font or stroke use default color of config if None
    fill: Optional[str] = "black" # Fill color for the segment
    title: Optional[str] = None   # Tooltip
    comment: Optional[str] = None
 
@dataclass
class SVGNodeConfig(SVGNode):
    """
    a single SVG Node configuration
    to display any element
    """
    x: float = 0.0
    y: float = 0.0 
    width: Optional[float] = None
    height: Optional[float] = None
    element_type: Optional[str] = None
    url: Optional[str] = None
    show_as_popup: bool = False  # Flag to indicate if the link should opened as a popup
    element_class: Optional[str] = "hoverable"

@dataclass
class Arc:
    radius: float
    start_x: float
    start_y: float
    end_x: float
    end_y: float

        
@dataclass
class DonutSegment(SVGNode):
    """
    A donut segment representing a
    section of a donut chart.
    """
    cx: float = 0.0
    cy: float = 0.0 
    inner_radius: float = 0.0
    outer_radius: float = 0.0
    start_angle: Optional[float] = 0.0
    end_angle: Optional[float] = 360.0
 
    @property
    def large_arc_flag(self) -> str:
        """
        Determine if the arc should be drawn as a large-arc (values >= 180 degrees).

        Returns:
            str: "1" if the arc is a large arc, otherwise "0".
        """
        large_arc_flag="1" if self.end_angle - self.start_angle >= 180 else "0"
        return large_arc_flag
    
    @property
    def start_angle_rad(self) -> float:
        return math.radians(self.start_angle)

    @property
    def end_angle_rad(self) -> float:
        return math.radians(self.end_angle)

    def get_arc(self, radial_offset: float = 0.5) -> Arc:
        # Calculate the adjusted radius within the bounds of inner and outer radii
        adjusted_radius = self.inner_radius + (self.outer_radius - self.inner_radius) * radial_offset
        
        # Calculate the start and end points of the arc
        start_x = self.cx + adjusted_radius * math.cos(self.start_angle_rad)
        start_y = self.cy + adjusted_radius * math.sin(self.start_angle_rad)
        end_x = self.cx + adjusted_radius * math.cos(self.end_angle_rad)
        end_y = self.cy + adjusted_radius * math.sin(self.end_angle_rad)

        return Arc(radius=adjusted_radius, start_x=start_x, start_y=start_y, end_x=end_x, end_y=end_y)

        
class SVG:
    """
    Class for creating SVG drawings.

    Attributes:
        config (SVGConfig): Configuration for the SVG drawing.
    """

    def __init__(self, config: SVGConfig = None):
        """
        Initialize SVG object with given configuration.

        Args:
            config (SVGConfig): Configuration for SVG generation.
        """
        self.config = config if config else SVGConfig()
        self.width = self.config.width
        self.height = self.config.height
        self.elements = []
        self.indent = self.config.indent

    @property
    def line_height(self)->float:
        # Calculate line height based on font size
        line_height = self.config.font_size * 1.2  # You can adjust this multiplier as needed
        return line_height
    
    def get_indent(self,level)->str:
        """
        get the indentation for the given level
        """
        indentation=f"{self.indent * level}"
        return indentation
    
    def get_svg_style(self, with_java_script: bool) -> str:
        """
        Define styles for SVG elements.
    
        Args:
            with_java_script (bool): Flag to indicate whether JavaScript-related styles should be included.
    
        Returns:
            str: String containing style definitions for SVG.
        """
        style = (
            f"{self.indent}<style>\n"
            f"{self.indent * 2}.hoverable {{ cursor: pointer; fill-opacity: 1; stroke: black; stroke-width: 0.5; }}\n"
            f"{self.indent * 2}.hoverable:hover {{ fill-opacity: 0.7; }}\n"
            f"{self.indent * 2}.selected {{ fill-opacity: 0.5; stroke: blue; stroke-width: 1.5;}}\n"
        )
    
        if with_java_script:
            style += (
                f"{self.indent * 2}.popup {{\n"
                f"{self.indent * 3}border: 2px solid black;\n"
                f"{self.indent * 3}border-radius: 15px;\n"
                f"{self.indent * 3}overflow: auto;\n"  # changed to 'auto' to allow scrolling only if needed
                f"{self.indent * 3}background: white;\n"
                f"{self.indent * 3}box-sizing: border-box;\n"  # ensures padding and border are included
                f"{self.indent * 3}padding: 10px;\n"  # optional padding inside the popup
                f"{self.indent * 3}height: 100%;\n"  # adjusts height relative to foreignObject
                f"{self.indent * 3}width: 100%;\n"  # adjusts width relative to foreignObject
                f"{self.indent * 2}}}\n"
                f"{self.indent * 2}.close-btn {{\n"  # style for the close button
                f"{self.indent * 3}cursor: pointer;\n"
                f"{self.indent * 3}position: absolute;\n"
                f"{self.indent * 3}top: 0;\n"
                f"{self.indent * 3}right: 0;\n"
                f"{self.indent * 3}padding: 5px;\n"
                f"{self.indent * 3}font-size: 20px;\n"
                f"{self.indent * 3}user-select: none;\n"  # prevents text selection on click
                f"{self.indent * 2}}}\n"
            )
        
        style += f"{self.indent}</style>\n"
        return style

    def get_text_width(self, text: str) -> int:
        """
        Estimate the width of a text string in the SVG based on the font size and font name.

        Args:
            text (str): The text content.

        Returns:
            int: The estimated width of the text in pixels.
        """
        average_char_width_factor = 0.6
        average_char_width = average_char_width_factor * self.config.font_size
        return int(average_char_width * len(text))  
    
    def get_text_rotation(self, rotation_angle: float) -> float:
        """
        Adjusts the rotation angle for SVG text elements to ensure that the text
        is upright and readable in a circular chart. The text will be rotated
        by 180 degrees if it is in the lower half of the chart (between 90 and 270 degrees).

        Args:
            rotation_angle (float): The initial rotation angle of the text element.

        Returns:
            float: The adjusted rotation angle for the text element.
        """
        # In the bottom half of the chart (90 to 270 degrees), the text
        # would appear upside down, so we rotate it by 180 degrees.
        if 90 <= rotation_angle < 270:
            rotation_angle -= 180

        # Return the adjusted angle. No adjustment is needed for the
        # top half of the chart as the text is already upright.
        return rotation_angle
    
    def get_donut_path(self, 
            segment: DonutSegment,
            radial_offset: float = 0.5,
            middle_arc:bool=False) -> str:
        """
        Create an SVG path definition for an arc using the properties of a DonutSegment.

        Args:
            segment (DonutSegment): The segment for which to create the path.
            radial_offset(float): 0 to 1 - useable in middle_arc mode
            middle_arc(bool): if True get the middle arc

        Returns:
            str: SVG path definition string for the full donut segment or the middle_arc if middle_arc is set to true.
        """ 
        if middle_arc:
            arc = segment.get_arc(radial_offset=radial_offset)
            
            # Create the path for the middle arc
            path_str = (
                f"M {arc.start_x} {arc.start_y} "  # Move to start of middle arc
                f"A {arc.radius} {arc.radius} 0 {segment.large_arc_flag} 1 {arc.end_x} {arc.end_y}"
            )
        else:
            outer_arc = segment.get_arc(radial_offset=1)
            inner_arc = segment.get_arc(radial_offset=0)
            path_str = (
                f"M {inner_arc.start_x} {inner_arc.start_y} "  # Move to start of inner arc
                f"L {outer_arc.start_x} {outer_arc.start_y} "  # Line to start of outer arc
                f"A {segment.outer_radius} {segment.outer_radius} 0 {segment.large_arc_flag} 1 {outer_arc.end_x} {outer_arc.end_y} "  # Outer arc
                f"L {inner_arc.end_x} {inner_arc.end_y} "  # Line to end of inner arc
                f"A {segment.inner_radius} {segment.inner_radius} 0 {segment.large_arc_flag} 0 {inner_arc.start_x} {inner_arc.start_y} "  # Inner arc (reverse)
                "Z"
            )
            
        return path_str

    def add_element(self, element: str, level: int = 1, comment: str = None):
        """
        Add an SVG element to the elements list with proper indentation.

        Args:
            element (str): SVG element to be added.
            level (int): Indentation level for the element.
            comment(str): optional comment to add
        """
        base_indent = self.get_indent(level)
        if comment:
            indented_comment = f"{base_indent}<!-- {comment} -->\n"
            self.elements.append(indented_comment)
        indented_element = f"{base_indent}{element}\n"
        self.elements.append(indented_element)

    def add_circle(self, config: SVGNodeConfig):
        """
        Add a circle element to the SVG, optionally making it clickable and with a hover effect.

        Args:
            config (SVGNodeConfig): Configuration for the circle element.
        """
        color = config.fill if config.fill else self.config.default_color
        circle_element = f'<circle cx="{config.x}" cy="{config.y}" r="{config.width}" fill="{color}" class="{config.element_class}" />'

        # If URL is provided, wrap the circle in an anchor tag to make it clickable
        if config.url:
            circle_indent = self.get_indent(config.indent_level + 1)
            circle_element = f"""<a xlink:href="{config.url}" target="_blank">
{circle_indent}{circle_element}
</a>"""

        # Use add_group to add the circle element with proper indentation
        self.add_group(
            circle_element,
            group_id=config.id,
            group_class=config.element_class,
            level=config.indent_level,
            comment=config.comment,
        )

    def add_rectangle(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        fill: str = None,
        indent_level: int = 1,
    ):
        """
        Add a rectangle element to the SVG.

        Args:
            x (int): X-coordinate of the rectangle's top-left corner.
            y (int): Y-coordinate of the rectangle's top-left corner.
            width (int): Width of the rectangle.
            height (int): Height of the rectangle.
            fill (str, optional): Fill color of the rectangle. Defaults to the default color.
            indent_level (int): Indentation level for the rectangle.
        """
        color = fill if fill else self.config.default_color
        rect = f'{self.get_indent(indent_level)}<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{color}" />\n'
        self.add_element(rect)

    def add_legend_column(
        self,
        items: List[Tuple[str, str]],
        title: str,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> None:
        """
        Add a legend column to the SVG.

        Args:
            items (List[Tuple[str, str]]): List of tuples with color code and label.
            title (str): Title of the legend.
            x (int): X position of the legend.
            y (int): Y position of the legend.
            width (int): Width of the color box in the legend.
            height (int): Height of each legend item.
        """
        self.add_text(x, y - height, title, font_weight="bold")
        for index, (color, label) in enumerate(items):
            self.add_rectangle(x, y + index * (height + 5), width, height, color)
            self.add_text(x + width + 10, y + index * (height + 5) + height / 2, label)

    def add_text(
        self,
        x: int,
        y: int,
        text: str,
        fill: str = "black",
        font_weight: str = "normal",
        text_anchor: str = "start",
        transform: str = "",
        centered: bool = False,
        indent_level: int =1,
    ) -> None:
        """
        Add text to the SVG.

        Args:
            x (int): X position of the text.
            y (int): Y position of the text.
            text (str): Text content.
            fill (str, optional): Fill color of the text. Defaults to "black".
            font_weight (str, optional): Font weight (normal, bold, etc.). Defaults to "normal".
            text_anchor (str, optional): Text alignment (start, middle, end). Defaults to "start".
            indent_level(int): the indentation level to apply
            centered (bool): If True, treat x and y as the center of the text. Default is False.
            transform (str, optional): Transformation for the text (e.g., rotation). Defaults to an empty string.
        """
        # Split the input text into lines
        lines = text.split('\n')
        total_text_height = self.line_height * len(lines)
        if centered:
            # Adjust text_anchor to 'middle' when centered
            text_anchor = "middle"
    
            # y-offset adjustment to center the text vertically
            y -= total_text_height // 2
        # Create a text element to hold the tspan elements
        # Only include the transform attribute if it is provided
        transform_attr = f'transform="{transform}" ' if transform else ""

        text_element = (
            f'\n{self.get_indent(indent_level)}<text x="{x}" y="{y}" fill="{fill}" '
            f'font-family="{self.config.font}" '
            f'font-size="{self.config.font_size}" '
            f'font-weight="{font_weight}" '
            f'text-anchor="{text_anchor}" '
            f'{transform_attr}>'
        )
        # Add tspan elements for each line
        for line in lines:
            escaped_line = html.escape(line)
            text_element += f'\n{self.get_indent(indent_level+1)}<tspan x="{x}" dy="{self.line_height}">{escaped_line}</tspan>'
    
        text_element += f"\n{self.get_indent(indent_level)}</text>\n"
        self.add_element(text_element)

    def add_group(
        self,
        content: str,
        group_id: str = None,
        group_class: str = None,
        level: int = 1,
        comment: str = None,
    ):
        """
        Add a group of elements to the SVG.

        Args:
            content (str): SVG content to be grouped.
            group_id (str, optional): ID for the group.
            group_class (str, optional): Class for the group.
            level (int): Indentation level for the group.
        """
        group_attrs = []
        if group_id:
            group_attrs.append(f'id="{group_id}"')
        if group_class:
            group_attrs.append(f'class="{group_class}"')
        attrs_str = " ".join(group_attrs)
        indented_content = "\n".join(
            f"{self.get_indent(level + 1)}{line}" for line in content.strip().split("\n")
        )
        group_str = f"{self.get_indent(level)}<g {attrs_str}>\n{indented_content}\n{self.get_indent(level)}</g>\n"
        self.add_element(group_str, level=level, comment=comment)

    def add_donut_segment(
        self,
        config: SVGNodeConfig,
        segment: DonutSegment,
    ) -> None:
        """
        Add a donut segment to the SVG.

        Args:
            config (SVGNodeConfig): Configuration for the donut segment.
            segment(DonutSegment)
        """
        color = config.fill if config.fill else self.config.default_color

        if color is None:
            color = self.config.default_color
            
        path_str=self.get_donut_path(segment)
     
        # Assemble the path and title elements
        path_element = f'<path d="{path_str}" fill="{color}" />\n'
        escaped_title = html.escape(config.title)  # Escape special characters

        title_element = f"<title>{escaped_title}</title>"

        # Combine path and title into one string without adding indentation here
        group_content = f"{path_element}{title_element}"

        # Check if the segment should be shown as a popup
        if config.show_as_popup:
            # Add JavaScript to handle popup logic
            onclick_action = f"onclick=\"showPopup('{config.url}', evt,this)\""
            group_content = f"<g {onclick_action}>{group_content}</g>"
        elif config.url:
            # Regular link behavior
            group_content = (
                f'<a xlink:href="{config.url}" target="_blank">{group_content}</a>'
            )

        # Use add_group to add the pie segment with proper indentation
        self.add_group(
            group_content,
            group_id=config.id,
            group_class=config.element_class,
            level=2,
            comment=config.comment,
        )

    def add_text_to_donut_segment(
        self,
        segment: DonutSegment,
        text: str,
        direction: str = "horizontal",
        color: str = "white",
        indent_level: int=1,
    ) -> None:
        """
        Add text to a donut segment with various direction options.

        Args:
            segment (DonutSegment): The donut segment to which text will be added.
            text (str): The text content to be added.
            direction (str): The direction in which the text should be drawn.
                             Options are "horizontal", "angled", or "curved".
            color (str): The color of the text. Default is "white".
        """
        # Common calculations
        mid_angle = (segment.start_angle + segment.end_angle) / 2
        mid_angle_rad = math.radians(mid_angle)
        mid_radius = (segment.inner_radius + segment.outer_radius) / 2
  
        if direction in ["horizontal", "angled"]:
            # Calculate position for horizontal or angled text
            text_x = segment.cx + mid_radius * math.cos(mid_angle_rad)
            text_y = segment.cy + mid_radius * math.sin(mid_angle_rad)

            # Adjust text anchor and rotation for better readability
            transform = ""
            if direction == "angled":
                rotation_angle = self.get_text_rotation(mid_angle)
                transform = f"rotate({rotation_angle}, {text_x}, {text_y})"

            # Add text using the add_text method
            self.add_text(
                x=text_x,
                y=text_y,
                text=text,
                fill=color,
                font_weight="normal",
                indent_level=indent_level,
                transform=transform,
                centered=True
            )

        elif direction == "curved":
            lines = text.split('\n')
            line_count = len(lines)
            total_text_height = self.line_height * line_count
    
            # Create a path for the text to follow
            path_id = f"path{segment.start_angle}-{segment.end_angle}"
            path_d = self.get_donut_path(segment, middle_arc=True)
            self.add_element(f'<path id="{path_id}" d="{path_d}" fill="none" stroke="none" />')
    
            # Calculate start offset for each line
            start_offset = 50 - (total_text_height / (2 * math.pi * mid_radius)) * 100 / line_count
    
            for line in lines:
                text_path_element = (
                    f'<text fill="{color}" font-family="{self.config.font}" font-size="{self.config.font_size}">'
                    f'<textPath xlink:href="#{path_id}" startOffset="{start_offset}%" text-anchor="middle">{html.escape(line)}</textPath>'
                    f"</text>"
                )
                self.add_element(text_path_element)
                start_offset += (self.line_height / (2 * math.pi * mid_radius)) * 100

        else:
            raise ValueError(f"invalid direction {direction}")

    def get_java_script(self) -> str:
        """
        get the java script code for interactive behavior
        """
        popup_script = """
    <script>
         function showPopup(url, evt,element) {
            // show a Popup fetching html content from the given url
            // for the given element
            // Handle the selection of the popup element
            selectPopupElement(element);
            var popup = document.getElementById('dcm-svg-popup');
            var iframe = document.getElementById('popup-iframe');
            var svgRect = evt.target.getBoundingClientRect();
            var svg = document.querySelector('svg');
            var svgPoint = svg.createSVGPoint();
            svgPoint.x = evt.clientX - svgRect.left;
            svgPoint.y = evt.clientY - svgRect.top;
        
            // Position the popup near the click event
            popup.setAttribute('x', svgPoint.x);
            popup.setAttribute('y', svgPoint.y);
            // Set the iframe src and make the popup visible
            iframe.setAttribute('src', url);
            popup.setAttribute('visibility', 'visible');
        }
        
        function selectPopupElement(element) {
            var popup = document.getElementById('dcm-svg-popup');
        
            // Deselect the current element if there is one
            if (popup.currentElement) {
                popup.currentElement.classList.remove('selected');
            }
        
            // Select the new element
            if (element) {
                element.classList.add('selected');
                popup.currentElement = element; // Update the reference to the currently selected element
            } else {
                popup.currentElement = null; // Clear the reference if no element is passed
            }
        }
        
        function closePopup() {
            var popup = document.getElementById('dcm-svg-popup');
            popup.setAttribute('visibility', 'hidden');
            // Deselect the element when the popup is closed
            selectPopupElement(null);
        }
    </script>
    """
        return popup_script

    def get_svg_markup(self, with_java_script: bool = False) -> str:
        """
        Generate the complete SVG markup.

        Args:
            with_java_script(bool): if True(default) the javascript code is included otherwise
            it's available via the get_java_script function

        Returns:
            str: String containing the complete SVG markup.
        """
        # Get current date and time
        now = datetime.now()
        formatted_now = now.strftime("%Y-%m-%d %H:%M:%S")
        header = (
            f"<!-- generated by dcm https://github.com/WolfgangFahl/dcm at {formatted_now} -->\n"
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{self.width}" height="{self.config.total_height}">\n'
        )
        popup = """
        <!-- Add a foreignObject for the popup -->
<foreignObject id="dcm-svg-popup" class="popup" width="500" height="354" x="150" y="260" visibility="hidden">
    <body xmlns="http://www.w3.org/1999/xhtml">
        <!-- Content of your popup goes here -->
        <div class="popup" style="background-color: white; border: 1px solid black; padding: 10px; box-sizing: border-box; width: 500px; height: 354px; position: relative;">
            <span onclick="closePopup()" class="close-btn">ⓧ</span>
            <iframe id="popup-iframe" width="100%" height="100%" frameborder="0"></iframe>
        </div>
    </body>
</foreignObject>
""" if with_java_script else ""
        styles = self.get_svg_style(with_java_script)
        body = "".join(self.elements)
        footer = "</svg>"
        java_script = self.get_java_script() if with_java_script else ""
        svg_markup = f"{header}{java_script}{styles}{body}{popup}{footer}"
        return svg_markup

    def save(self, filename: str):
        """
        Save the SVG markup to a file.

        Args:
            filename (str): Filename to save the SVG markup.
        """
        with open(filename, "w") as file:
            file.write(self.get_svg_markup())
