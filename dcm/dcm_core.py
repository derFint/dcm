"""
Created on 2023-06-11

@author: wf
"""
import json
import markdown2
import os
from dataclasses import dataclass, field
from json.decoder import JSONDecodeError
from typing import Dict, List, Optional, Tuple, Union

import yaml
from dataclasses_json import dataclass_json

from dcm.svg import SVG, SVGConfig, SVGNodeConfig


@dataclass_json
@dataclass
class CompetenceElement:
    """
    A base class representing a generic competence element with common properties.

    Attributes:
        name (str): The name of the competence element.
        id (Optional[str]): An optional identifier for the competence element.
        url (Optional[str]): An optional URL for more information about the competence element.
        description (Optional[str]): An optional description of the competence element.
        color_code (str): A string representing a color code associated with the competence element.
    """

    name: str
    id: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    color_code: Optional[str] = None
    
    def as_html(self)->str:
        """
        convert me to html
        
        Returns:
            str: html markup
        """
        html=f"<h2>{self.name}</h2>"
        if self.description:
            desc_html=markdown2.markdown(self.description, extras=["fenced-code-blocks", "tables", "spoiler"])
            html=html+"\n"+desc_html
        return html

    def to_svg_node_config(self, **kwargs) -> SVGNodeConfig:
        """
        convert me to an SVGNode Configuration
        """
        element_type = f"{self.__class__.__name__}"
        comment = f"{element_type}:{self.description}"
        svg_node_config = SVGNodeConfig(
            # @TODO prepend {element_type}:
            id=f"{self.id}",
            url=self.url,
            fill=self.color_code,
            title=self.name,
            comment=comment,
            **kwargs,
        )
        return svg_node_config


@dataclass_json
@dataclass
class CompetenceFacet(CompetenceElement):
    """
    Represents a specific facet of a competence aspect, inheriting from CompetenceElement.

    This class can include additional properties or methods specific to a competence facet.
    """

    # Since all properties are inherited, no additional properties are defined here.

@dataclass_json
@dataclass
class CompetenceAspect(CompetenceElement):
    """
    Represents a broader category of competence, which includes various facets.

    Attributes:
        facets (List[CompetenceFacet]): A list of CompetenceFacet objects representing individual facets of this aspect.
    """

    facets: List[CompetenceFacet] = field(default_factory=list)
    credits: Optional[int] = None


@dataclass_json
@dataclass
class CompetenceLevel(CompetenceElement):
    """
    Defines a specific level of competence within the framework.

    Attributes:
        level (int): level number starting from 1 as the lowest and going up to as many level as defined for the CompetenceTree
    """

    level: int = 1


@dataclass_json
@dataclass
class CompetenceTree(CompetenceElement):
    """
    Represents the entire structure of competencies, including various aspects and levels.

    Attributes:
        competence_aspects (Dict[str, CompetenceAspect]): A dictionary mapping aspect IDs to CompetenceAspect objects.
        competence_levels (List[CompetenceLevel]): A list of CompetenceLevel objects representing the different levels in the competence hierarchy.
        element_names (Dict[str, str]): A dictionary holding the names for tree, aspects, facets, and levels.  The key is the type ("tree", "aspect", "facet", "level").
    """

    competence_aspects: Dict[str, CompetenceAspect] = field(default_factory=dict)
    competence_levels: List[CompetenceLevel] = field(default_factory=list)
    element_names: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def required_keys(cls) -> Tuple:
        keys = {"name", "id", "url", "description", "element_names"}
        return keys

    def to_pretty_json(self):
        """
        Converts the CompetenceTree object to a pretty JSON string, handling null values.
        """
        json_str = self.to_json()
        json_dict = json.loads(json_str)

        def remove_none_values(data):
            """
            Recursively removes keys with None values from a dictionary, list, or nested structure.
            """
            if isinstance(data, dict):
                return {
                    k: remove_none_values(v) for k, v in data.items() if v is not None
                }
            elif isinstance(data, list):
                return [remove_none_values(item) for item in data]
            return data

        none_free_dict = remove_none_values(json_dict)
        null_free_json_str = json.dumps(none_free_dict, indent=2)
        return null_free_json_str

    def add_legend(self, svg: SVG) -> None:
        """
        Add a legend to the SVG explaining the color codes for levels and aspects.
        Args:
            svg (SVG): The SVG object to which the legend will be added.
        """
        # Starting x position for the legends, starting 10 pixels from the left edge
        x_start = 10
        # y position for the legends, starting 20 pixels from the bottom edge
        y = svg.config.total_height - svg.config.legend_height + 20
        # Width and height of each legend color box
        box_width, box_height = 30, 20
        # Padding between legend items and between the color box and the text
        padding = 5

        # Add the competence level legend
        level_items = [
            (level.color_code, level.name) for level in self.competence_levels
        ]
        svg.add_legend_column(
            level_items,
            self.element_names.get("level", "Level"),
            x_start,
            y,
            box_width,
            box_height,
        )

        # Calculate the x position for the aspect legend based on the width of the level legend
        x_aspect_start = (
            x_start
            + box_width
            + padding
            + max(svg.get_text_width(level.name) for level in self.competence_levels)
            + padding
        )

        # Add the competence aspect legend
        aspect_items = [
            (aspect.color_code, aspect.name)
            for aspect in self.competence_aspects.values()
        ]
        svg.add_legend_column(
            aspect_items,
            self.element_names.get("aspect", "Aspect"),
            x_aspect_start,
            y,
            box_width,
            box_height,
        )


@dataclass_json
@dataclass
class Achievement:
    """
    Class representing an individual's achievement level for a specific competence facet.

    Attributes:
        facet_id (str): Identifier for the competence facet.
        level (int): The achieved level for this facet.
        percent(float): how well was the achievement reached?
        evidence (Optional[str]): Optional evidence supporting the achievement.
        date_assessed (Optional[str]): Optional date when the achievement was assessed (ISO-Format).
    """

    facet_id: str
    level: int
    score: float
    score_unit: Optional[str] = "%"
    evidence: Optional[str] = None
    date_assessed: Optional[str] = None


@dataclass
@dataclass_json
class Student:
    """
    A student with achievements.
    Attributes:
        student_id (str): Identifier for the student.
        achievements (Dict[str, List[Achievement]]): A dictionary where each key is a competence tree identifier
                                                     and the value is a list of Achievement instances for that tree.
    """

    student_id: str
    achievements: Dict[str, List[Achievement]]

    @classmethod
    def required_keys(cls):
        keys = {"achievements"}
        return keys


class DynamicCompetenceMap:
    """
    a visualization of a competence map
    """

    def __init__(self, competence_tree: CompetenceTree):
        """
        constructor
        """
        self.competence_tree = competence_tree
        
    def lookup(self, aspect_name: str, facet_name: str) -> Optional[CompetenceFacet]:
        """
        Look up a facet within a specified aspect by their names.

        Args:
            aspect_name (str): The name of the aspect to search within.
            facet_name (str): The name of the facet to find.

        Returns:
            Optional[CompetenceFacet]: The found facet, or None if not found.
        """
        ct=self.competence_tree
        aspect = ct.competence_aspects.get(aspect_name)
        if aspect:
            for facet in aspect.facets:
                if facet.name == facet_name:
                    return facet
        return None

    @classmethod
    def examples_path(cls) -> str:
        # the root directory (default: examples)
        path = os.path.join(os.path.dirname(__file__), "../dcm_examples")
        path = os.path.abspath(path)
        return path

    @classmethod
    def get_example_dcm_definitions(cls, markup: str = 'json', required_keys: Optional[Tuple] = None, as_text: bool = True) -> dict:
        """
        Retrieve example Dynamic Competence Map (DCM) definitions from files in the specified markup format (either JSON or YAML).
    
        Args:
            markup (str): The markup format of the input files. Defaults to 'json'. Supported values are 'json' and 'yaml'.
            required_keys (Optional[Tuple]): A tuple of keys required to validate the data. If not provided, all keys will be considered valid.
            as_text (bool): If True, returns the file content as text; if False, returns parsed data. Defaults to True.
    
        Returns:
            dict: A dictionary where each key is the prefix of the file name and the value is the file content as text or parsed data, depending on the value of 'as_text'.
    
        Raises:
            Exception: If there's an error in reading or parsing the file, or if the file does not meet the required validation criteria.
        """
        example_dcm_defs = {}
        file_ext=f".{markup}"
        examples_path = cls.examples_path()
        for dirpath, _dirnames, filenames in os.walk(examples_path):
            for filename in filenames:
                if filename.endswith(file_ext):
                    filepath = os.path.join(dirpath, filename)
                    with open(filepath, "r") as definition_file:
                        file_prefix = filename.replace(file_ext, "")
                        definition_text = definition_file.read()
                        try:
                            definition_data = cls.parse_markup(definition_text, markup)
                            if cls.is_valid_definition(definition_data, required_keys):
                                if as_text:
                                    example_dcm_defs[file_prefix] = definition_text
                                else:
                                    example_dcm_defs[file_prefix] = definition_data   
                        except Exception as ex:
                            cls.handle_markup_issue(filename, definition_text, ex)
        return example_dcm_defs
    
    @classmethod
    def parse_markup(cls, text: str, markup: str) -> Union[dict, list]:
        """
        Parse the given text as JSON or YAML based on the specified markup type.
    
        Args:
            text (str): The string content to be parsed.
            markup (str): The type of markup to use for parsing. Supported values are 'json' and 'yaml'.
    
        Returns:
            Union[dict, list]: The parsed data, which can be either a dictionary or a list, depending on the content.
    
        Raises:
            ValueError: If an unsupported markup format is specified.
        """
        if markup == 'json':
            return json.loads(text)
        elif markup == 'yaml':
            return yaml.safe_load(text)
        else:
            raise ValueError(f"Unsupported markup format: {markup}")

    
    @classmethod
    def handle_markup_issue(cls, name: str, definition_string: str, ex, markup):
        if isinstance(ex, JSONDecodeError):
            lines = definition_string.splitlines()  # Split the string into lines
            err_line = lines[ex.lineno - 1]  # JSONDecodeError gives 1-based lineno
            pointer = (
                " " * (ex.colno - 1) + "^"
            )  # Create a pointer string to indicate the error position
            error_message = (
                f"{name}:JSON parsing error on line {ex.lineno} column {ex.colno}:\n"
                f"{err_line}\n"
                f"{pointer}\n"
                f"{ex.msg}"
            )
            raise ValueError(error_message)  # Raise a new exception with this message
        else:
            error_message = f"error in {name}: {str(ex)}"
            raise ValueError(error_message)

    @classmethod
    def is_valid_definition(cls, definition_data, required_keys: Tuple):
        return all(key in definition_data for key in required_keys)

    @classmethod
    def get_examples(cls, content_class=CompetenceTree, markup:str='json') -> dict:
        examples = {}
        for name, definition_string in cls.get_example_dcm_definitions(
            required_keys=content_class.required_keys(),
            markup=markup
        ).items():
            dcm = cls.from_definition_string(name, definition_string, content_class,markup=markup)
            examples[name] = dcm
        return examples
            
    @classmethod
    def from_definition_string(cls, name: str, definition_string: str, content_class, markup: str = 'json') -> "DynamicCompetenceMap":
        """
        Load a DynamicCompetenceMap instance from a definition string (either JSON or YAML).

        Args:
            name (str): A name identifier for the data source.
            definition_string (str): The string content of the definition.
            content_class (dataclass_json): The class which will be instantiated with the parsed data.
            markup (str): The markup format of the data. Defaults to 'json'. Supported values are 'json' and 'yaml'.

        Returns:
            DynamicCompetenceMap: An instance of DynamicCompetenceMap loaded with the parsed data.

        Raises:
            ValueError: If there's an error in parsing the data.
        """
        try:
            data = cls.parse_markup(definition_string, markup)
            content = content_class.from_dict(data)
            return DynamicCompetenceMap(content)
        except Exception as ex:
            cls.handle_markup_issue(name, definition_string, ex, markup)


    def generate_svg(
        self, filename: Optional[str] = None, config: Optional[SVGConfig] = None
    ) -> str:
        """
        Generate the SVG markup and optionally save it to a file. If a filename is given, the method
        will also save the SVG to that file. The SVG is generated based on internal state not shown here.

        Args:
            filename (str, optional): The path to the file where the SVG should be saved. Defaults to None.
            config (SVGConfig, optional): The configuration for the SVG canvas and legend. Defaults to default values.

        Returns:
            str: The SVG markup.
        """
        if config is None:
            config = SVGConfig()  # Use default configuration if none provided
        svg_markup = self.generate_svg_markup(self.competence_tree, config)
        if filename:
            self.save_svg_to_file(svg_markup, filename)
        return svg_markup

    def generate_svg_markup(
        self, competence_tree: CompetenceTree = None, config: SVGConfig = None
    ) -> str:
        """
        Generate SVG markup based on the provided competence tree and configuration.

        Args:
            competence_tree (CompetenceTree): The competence tree structure containing the necessary data.
            config (SVGConfig): The configuration for the SVG canvas and legend.

        Returns:
            str: The generated SVG markup.
        """
        if competence_tree is None:
            competence_tree = self.competence_tree
        competence_aspects = competence_tree.competence_aspects
        # Instantiate the SVG class
        svg = SVG(config)
        # use default config incase config was None
        config = svg.config

        # Center of the donut
        # Center of the donut chart should be in the middle of the main SVG area, excluding the legend
        cx = svg.width // 2
        cy = (config.total_height - config.legend_height) // 2  # Adjusted for legend

        # Calculate the radius for the central circle (10% of the width)
        tree_radius = cx / 9

        # Add the central circle representing the CompetenceTree
        circle_config = competence_tree.to_svg_node_config(
            x=cx, y=cy, width=tree_radius
        )
        svg.add_circle(config=circle_config)

        facet_radius = min(cx, cy) * 0.9  # Leave some margin
        aspect_radius = facet_radius / 3  # Choose a suitable inner radius

        # Total number of facets
        total_facets = sum(len(aspect.facets) for aspect in competence_aspects.values())

        # Starting angle for the first aspect
        aspect_start_angle = 0

        for aspect_code, aspect in competence_aspects.items():
            num_facets_in_aspect = len(aspect.facets)

            # Skip aspects with no facets
            if num_facets_in_aspect == 0:
                continue
            aspect_angle = (num_facets_in_aspect / total_facets) * 360
            aspect_config = aspect.to_svg_node_config(
                x=cx,
                y=cy,
                width=tree_radius,  # inner radius
                height=aspect_radius,  # outer radius
            )
            # fix id
            aspect_config.id = aspect_code
            # Draw the aspect segment as a donut segment
            svg.add_donut_segment(
                config=aspect_config,
                start_angle_deg=aspect_start_angle,
                end_angle_deg=aspect_start_angle + aspect_angle,
            )

            facet_start_angle = (
                aspect_start_angle  # Facets start where the aspect starts
            )
            angle_per_facet = (
                aspect_angle / num_facets_in_aspect
            )  # Equal angle for each facet

            for facet in aspect.facets:
                # Add the facet segment as a donut segment
                facet_config = facet.to_svg_node_config(
                    x=cx,
                    y=cy,
                    width=aspect_radius,  # inner radius
                    height=facet_radius,  # outer radius
                )
                svg.add_donut_segment(
                    config=facet_config,
                    start_angle_deg=facet_start_angle,
                    end_angle_deg=facet_start_angle + angle_per_facet,
                )
                facet_start_angle += angle_per_facet

            aspect_start_angle += aspect_angle

        # optionally add legend
        if config.legend_height > 0:
            self.competence_tree.add_legend(svg)

        # Return the SVG markup
        return svg.get_svg_markup()

    def save_svg_to_file(self, svg_markup: str, filename: str):
        # Save the SVG content to a file
        with open(filename, "w") as file:
            file.write(svg_markup)
