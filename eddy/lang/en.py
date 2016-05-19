##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <danielepantaleone@me.com>      #
#                                                                        #
#  This program is free software: you can redistribute it and/or modify  #
#  it under the terms of the GNU General Public License as published by  #
#  the Free Software Foundation, either version 3 of the License, or     #
#  (at your option) any later version.                                   #
#                                                                        #
#  This program is distributed in the hope that it will be useful,       #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the          #
#  GNU General Public License for more details.                          #
#                                                                        #
#  You should have received a copy of the GNU General Public License     #
#  along with this program. If not, see <http://www.gnu.org/licenses/>.  #
#                                                                        #
#  #####################                          #####################  #
#                                                                        #
#  Graphol is developed by members of the DASI-lab group of the          #
#  Dipartimento di Ingegneria Informatica, Automatica e Gestionale       #
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it  #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


#############################################
# ACTIONS
#################################

ACTION_ABOUT_N = 'About {0}'
ACTION_BRING_TO_FRONT_N = 'Bring to Front'
ACTION_CENTER_DIAGRAM_N = 'Center diagram'
ACTION_CLOSE_PROJECT_N = 'Close'
ACTION_COMPOSE_PROPERTY_DOMAIN_N = 'Domain'
ACTION_COMPOSE_PROPERTY_RANGE_N = 'Range'
ACTION_COPY_N = 'Copy'
ACTION_CUT_N = 'Cut'
ACTION_DELETE_N = 'Delete'
ACTION_DELETE_CONFIRM_N = 'Delete...'
ACTION_DIAG_WEBSITE_N = 'DIAG - Sapienza University'
ACTION_DIAGRAM_PROPERTIES_N = 'Properties...'
ACTION_EDGE_SWAP_N = 'Swap'
ACTION_EXPORT_N = 'Export...'
ACTION_GRAPHOL_WEBSITE_N = 'Visit Graphol website'
ACTION_IMPORT_N = 'Import...'
ACTION_NEW_DIAGRAM_N = 'New diagram...'
ACTION_NODE_PROPERTIES_N = 'Properties...'
ACTION_OPEN_N = 'Open...'
ACTION_OPEN_PREFERENCES_N = 'Preferences'
ACTION_PASTE_N = 'Paste'
ACTION_PRINT_N = 'Print...'
ACTION_QUIT_N = 'Quit'
ACTION_REFACTOR_NAME_N = 'Rename...'
ACTION_RELOCATE_LABEL_N = 'Relocate label'
ACTION_REMOVE_EDGE_BREAKPOINT_N = 'Remove breakpoint'
ACTION_RENAME_DIAGRAM_N = 'Rename...'
ACTION_SAVE_N = 'Save'
ACTION_SAVE_AS_N = 'Save As...'
ACTION_SELECT_ALL_N = 'Select all'
ACTION_SEND_TO_BACK_N = 'Send to Back'
ACTION_SNAP_TO_GRID_N = 'Snap to grid'
ACTION_SYNTAX_CHECK_N = 'Run syntax validation'
ACTION_TOGGLE_EDGE_COMPLETE_N = 'Complete'

ACTION_ABOUT_S = 'About {0}'
ACTION_BRING_TO_FRONT_S = 'Bring selected items to front'
ACTION_CENTER_DIAGRAM_S = 'Center the active diagram'
ACTION_CLOSE_PROJECT_S = 'Close the current project'
ACTION_COPY_S = 'Copy selected items'
ACTION_CUT_S = 'Cut selected items'
ACTION_DELETE_S = 'Delete selected items'
ACTION_EXPORT_S = 'Export the current project'
ACTION_IMPORT_S = 'Import a document in the current project'
ACTION_NEW_DIAGRAM_S = 'Create a new diagram'
ACTION_OPEN_S = 'Open a diagram and add it to the current project'
ACTION_PASTE_S = 'Paste previously copied items'
ACTION_PRINT_S = 'Print the current project'
ACTION_QUIT_S = 'Quit {0}'
ACTION_SAVE_S = 'Save the current project'
ACTION_SAVE_AS = 'Create a copy of the active diagram'
ACTION_SELECT_ALL_S = 'Select all items in the active diagram'
ACTION_SEND_TO_BACK_S = 'Send selected items to back'
ACTION_SNAP_TO_GRID_S = 'Snap diagram elements to the grid'
ACTION_SYNTAX_CHECK_S = 'Run syntax validation on the current project'

#############################################
# UNDO / REDO COMMANDS
#################################

COMMAND_COMPOSE_DOMAIN_RANGE_RESTRICTION = 'compose {0} {1}'
COMMAND_DIAGRAM_CENTER = 'center diagram'
COMMAND_DIAGRAM_EDIT_PROPERTIES = 'edit {0} properties'
COMMAND_DIAGRAM_RESIZE = 'resize diagram'
COMMAND_EDGE_ADD = 'add {0}'
COMMAND_EDGE_ANCHOR_MOVE = 'move {0} anchor point'
COMMAND_EDGE_BREAKPOINT_ADD = 'add {0} breakpoint'
COMMAND_EDGE_BREAKPOINT_MOVE = 'move {0} breakpoint'
COMMAND_EDGE_BREAKPOINT_REMOVE = 'remove {0} breakpoint'
COMMAND_EDGE_SWAP = 'swap {0}'
COMMAND_EDGE_SWAP_MULTI = 'swap {0} edges'
COMMAND_EDGE_TOGGLE_COMPLETE = 'toggle {0} completness'
COMMAND_EDGE_TOGGLE_COMPLETE_MULTI = 'toggle completness for {0} edges'
COMMAND_ITEM_TRANSLATE = 'move {0} item(s)'
COMMAND_ITEM_ADD = 'add {0}'
COMMAND_ITEM_ADD_MULTI = 'add {0} items'
COMMAND_ITEM_REMOVE = 'remove {0}'
COMMAND_ITEM_REMOVE_MULTI = 'remove {0} items'
COMMAND_ITEM_SET_PROPERTY = '{0}set {1} {2} property'
COMMAND_NODE_ADD = 'add {0}'
COMMAND_NODE_CHANGE_INPUTS_ORDER = 'change {0} inputs order'
COMMAND_NODE_CHANGE_META = 'change {0} metadata'
COMMAND_NODE_EDIT_LABEL = 'edit {0} label'
COMMAND_NODE_EDIT_PROPERTIES = 'edit {0} properties'
COMMAND_NODE_MOVE = 'move {0}'
COMMAND_NODE_MOVE_LABEL = 'move {0} label'
COMMAND_NODE_MOVE_MULTI = 'move {0} nodes'
COMMAND_NODE_OPERATOR_SWITCH = 'switch {0} to {1}'
COMMAND_NODE_REFACTOR_NAME = 'change predicate "{0}" to "{1}"'
COMMAND_NODE_RESIZE = 'resize {0}'
COMMAND_NODE_SET_BRUSH = 'set {0} brush on {1} node(s)'
COMMAND_NODE_SET_DATATYPE = 'change {0} to {1}'
COMMAND_NODE_SET_DEPTH = 'change {0} depth'
COMMAND_NODE_SET_FACET = 'change {0} to {1}'
COMMAND_NODE_SET_INDIVIDUAL_AS = 'change {0} to {1}'
COMMAND_NODE_SET_PROPERTY_RESTRICTION = 'change {0} to {1}'
COMMAND_NODE_SET_SPECIAL = 'change {0} to {1}'
COMMAND_NODE_SET_VALUE = 'change value to {0}'
COMMAND_PROJECT_SET_PREFIX = "set project prefix to '{0}'"
COMMAND_PROJECT_SET_IRI = "set project IRI to '{0}'"

#############################################
# DIAGRAM CREATE / EDIT / LOAD / DELETE
#################################

DIAGRAM_CAPTION_ALREADY_EXISTS = "Diagram '{0}' already exists!"
DIAGRAM_CAPTION_NAME_NOT_VALID = "'{0}' is not a valid diagram name!"
DIAGRAM_CREATION_FAILED_WINDOW_TITLE = 'Diagram creation failed!'
DIAGRAM_CREATION_FAILED_MESSAGE = 'Eddy could not create the specified diagram: {0}!'
DIAGRAM_DIALOG_LOCATION_LABEL = 'Location'
DIAGRAM_DIALOG_NAME_LABEL = 'Name'
DIAGRAM_DIALOG_NEW_WINDOW_TITLE = 'New diagram'
DIAGRAM_DIALOG_RENAME_WINDOW_TITLE = 'Rename diagram'
DIAGRAM_LOAD_FAILED_WINDOW_TITLE = 'Diagram load failed!'
DIAGRAM_LOAD_FAILED_MESSAGE = 'Eddy could not load the specified diagram: {0}!'
DIAGRAM_REMOVE_POPUP_TITLE = 'Remove diagram: {0}?'
DIAGRAM_REMOVE_POPUP_INFORMATIVE_TEXT = '<b>NOTE: This action is not reversible!</b>'
DIAGRAM_REMOVE_POPUP_QUESTION = 'Are you sure you want to remove diagram <b>{0}</b>? If you continue, ' \
                                'all the predicates that have been defined only in this diagram will be lost!'

#############################################
# DIAGRAM IMPORT
#################################

DIAGRAM_IMPORT_FAILED_WINDOW_TITLE = 'Diagram import failed!'
DIAGRAM_IMPORT_FAILED_MESSAGE = 'Eddy could not import the specified file: {0}!'
DIAGRAM_IMPORT_PROGRESS_TITLE = 'Importing {0}...'
DIAGRAM_IMPORT_PARTIAL_WINDOW_TITLE = 'Partial document import!'
DIAGRAM_IMPORT_PARTIAL_INFORMATIVE_MESSAGE = 'If needed, <a href="{0}">submit a bug report</a> with detailed information.'
DIAGRAM_IMPORT_PARTIAL_MESSAGE = 'Document <b>{0}</b> has been imported! However some errors (<b>{1}</b>) have ' \
                                 'been generated during the import process. You can inspect detailed ' \
                                 'information by expanding the box below.'

#############################################
# DOCK WIDGETS
#################################

DOCK_ONTOLOGY_EXPLORER = 'Ontology Explorer'
DOCK_INFO = 'Info'
DOCK_OVERVIEW = 'Overview'
DOCK_PALETTE = 'Palette'
DOCK_PROJECT_EXPLORER = 'Project Explorer'

#############################################
# EXCEPT_HOOK_MESSAGE
#################################

EXCEPT_HOOK_BTN_CLOSE = 'Close'
EXCEPT_HOOK_BTN_QUIT = 'Quit {0}'
EXCEPT_HOOK_INFORMATIVE_MESSAGE = 'If the problem persists please <a href="{0}">submit a bug report</a>.'
EXCEPT_HOOK_MESSAGE = 'This is embarrassing ...\n\n' \
                      'A critical error has just occurred. ' \
                      '{0} will continue to work, however a reboot is highly recommended.'

#############################################
# FORMS
#################################

FORM_CARDINALITY_ERROR_WINDOW_TITLE = 'Invalid range specified'
FORM_CARDINALITY_ERROR_MESSAGE = 'Min. cardinality <b>{0}</b> must be lower or equal than Max. cardinality <b>{1}</b>'
FORM_CARDINALITY_LABEL_MIN = 'Min. cardinality'
FORM_CARDINALITY_LABEL_MAX = 'Max. cardinality'
FORM_CARDINALITY_WINDOW_TITLE = 'Insert cardinality'
FORM_VALUE_WINDOW_TITLE = 'Compose value'
FORM_VALUE_LABEL_DATATYPE = 'Datatype'
FORM_VALUE_LABEL_VALUE = 'Value'

#############################################
# INFO BOX
#################################

INFO_HEADER_ASSERTIONS = 'Assertions'
INFO_HEADER_ATOMIC_PREDICATES = 'Atomic predicates'
INFO_HEADER_GENERAL = 'General'
INFO_HEADER_NODE_PROPERTIES = 'Node properties'
INFO_HEADER_ONTOLOGY_PROPERTIES = 'Ontology properties'
INFO_HEADER_PREDICATE_PROPERTIES = 'Predicate properties'

INFO_KEY_ASYMMETRIC = 'Asymmetric'
INFO_KEY_ATTRIBUTE = 'Attribute'
INFO_KEY_COLOR = 'Color'
INFO_KEY_COMPLETE = 'Complete'
INFO_KEY_CONCEPT = 'Concept'
INFO_KEY_DATATYPE = 'Datatype'
INFO_KEY_FACET = 'Facet'
INFO_KEY_FUNCTIONAL = 'Funct.'
INFO_KEY_ID = 'ID'
INFO_KEY_IDENTITY = 'Identity'
INFO_KEY_INCLUSION = 'Inclusion'
INFO_KEY_INVERSE_FUNCTIONAL = 'Inv. Funct.'
INFO_KEY_IRREFLEXIVE = 'Irreflexive'
INFO_KEY_IRI = 'IRI'
INFO_KEY_LABEL = 'Label'
INFO_KEY_MEMBERSHIP = 'Membership'
INFO_KEY_NAME = 'Name'
INFO_KEY_PREFIX = 'Prefix'
INFO_KEY_REFLEXIVE = 'Reflexive'
INFO_KEY_RESTRICTION = 'Restriction'
INFO_KEY_ROLE = 'Role'
INFO_KEY_SOURCE = 'Source'
INFO_KEY_SYMMETRIC = 'Symmetric'
INFO_KEY_TARGET = 'Target'
INFO_KEY_TRANSITIVE = 'Transitive'
INFO_KEY_TYPE = 'Type'
INFO_KEY_VALUE = 'Value'

#############################################
# MENUS
#################################

MENU_COMPOSE = 'Compose'
MENU_EDIT = 'Edit'
MENU_FILE = 'File'
MENU_HELP = 'Help'
MENU_REFACTOR = 'Refactor'
MENU_REFACTOR_BRUSH = 'Select color'
MENU_SET_BRUSH = 'Select color'
MENU_SET_DATATYPE = 'Select type'
MENU_SET_FACET = 'Select facet'
MENU_SET_INDIVIDUAL_AS = 'Set as'
MENU_SET_PROPERTY_RESTRICTION = 'Select restriction'
MENU_SET_SPECIAL = 'Special type'
MENU_SWITCH_OPERATOR = 'Switch to'
MENU_TOOLBARS = 'Toolbars'
MENU_TOOLS = 'Tools'
MENU_VIEW = 'View'

#############################################
# META
#################################

META_HEADER_ASYMMETRIC = 'Asymmetric'
META_HEADER_FUNCTIONAL = 'Functional'
META_HEADER_INVERSE_FUNCTIONAL = 'Inverse Functional'
META_HEADER_IRREFLEXIVE = 'Irreflexive'
META_HEADER_PREDICATE = 'Predicate'
META_HEADER_REFLEXIVE = 'Reflexive'
META_HEADER_SYMMETRIC = 'Symmetric'
META_HEADER_TRANSITIVE = 'Transitive'
META_HEADER_TYPE = 'Type'

#############################################
# ONTOLOGY EXPLORER
#################################

ONTO_EXPLORER_SEARCH_PLACEHOLDER = 'Search...'

#############################################
# PROJECT DIALOG / LOADING / SAVING
#################################

PROJECT_CAPTION_ALREADY_EXISTS = "Project '{0}' already exists!"
PROJECT_CAPTION_NAME_NOT_VALID = "'{0}' is not a valid project name!"
PROJECT_CLOSING_SAVE_CHANGES_MESSAGE = 'Your project contains unsaved changes: do you want to save?'
PROJECT_CLOSING_SAVE_CHANGES_WINDOW_TITLE = 'Save changes?'
PROJECT_IRI_LABEL = 'IRI'
PROJECT_LOADING = 'Loading project: {0}'
PROJECT_LOCATION_LABEL = 'Location'
PROJECT_NAME_LABEL = 'Name'
PROJECT_PREFIX_LABEL = 'Prefix'
PROJECT_SAVE_FAILED_WINDOW_TITLE = 'Save failed!'
PROJECT_SAVE_FAILED_MESSAGE = 'Eddy could not save the current project!'
PROJECT_WINDOW_TITLE = 'New project'

#############################################
# PROJECT EXPORT [OWL] DIALOG
#################################

PROJECT_EXPORT_OWL_WINDOW_TITLE = 'OWL Export'
PROJECT_EXPORT_OWL_SYNTAX_KEY = 'Syntax'
PROJECT_EXPORT_OWL_MALFORMED_EXPRESSION_WINDOW_TITLE = 'Malformed expression'
PROJECT_EXPORT_OWL_MALFORMED_EXPRESSION_MESSAGE = 'Malformed expression detected on {0}: {1}'
PROJECT_EXPORT_OWL_MALFORMED_EXPRESSION_QUESTION = 'Do you want to see the error in the diagram?'
PROJECT_EXPORT_OWL_ERRORED_WINDOW_TITLE = 'Unhandled exception!'
PROJECT_EXPORT_OWL_ERRORED_MESSAGE = 'Diagram translation could not be completed!'
PROJECT_EXPORT_OWL_ERRORED_INFORMATIVE_MESSAGE = 'Please <a href="{0}">submit a bug report</a> with detailed information.'
PROJECT_EXPORT_OWL_COMPLETED_WINDOW_TITLE = 'Translation completed!'
PROJECT_EXPORT_OWL_COMPLETED_MESSAGE = 'Do you want to open the OWL ontology?'
PROJECT_EXPORT_OWL_DISCONNECTED_FACET = 'disconnected facet node'
PROJECT_EXPORT_OWL_MISMATCH_INCLUSION = 'type mismatch in inclusion'
PROJECT_EXPORT_OWL_MISMATCH_EQUIVALENCE = 'type mismatch in equivalence'
PROJECT_EXPORT_OWL_MISMATCH_MEMBERSHIP = 'type mismatch in membership'
PROJECT_EXPORT_OWL_MISSING_CARDINALITY = 'missing cardinality'
PROJECT_EXPORT_OWL_MISSING_OPERAND = 'missing operand(s)'
PROJECT_EXPORT_OWL_MISSING_FACET = 'missing facet node(s)'
PROJECT_EXPORT_OWL_MISSING_VALUE_DOMAIN = 'missing value domain node'
PROJECT_EXPORT_OWL_TOO_MANY_OPERANDS = 'too many operands'
PROJECT_EXPORT_OWL_UNSUPPORTED_OPERAND = 'unsupported operand ({0})'
PROJECT_EXPORT_OWL_UNSUPPORTED_RESTRICTION = 'unsupported restriction'
PROJECT_EXPORT_OWL_UNSUPPORTED_SYNTAX = 'unsupported syntax ({0})'

#############################################
# PREFERENCES DIALOG
#################################

PREFERENCES_FIELD_DIAGRAM_SIZE_TOOLTIP = 'This setting changes the default size of all the newly created diagrams.'
PREFERENCES_FIELD_LANGUAGE_TOOLTIP = 'This setting changes the language of {0} (reboot required).'
PREFERENCES_LABEL_DIAGRAM_SIZE = 'Diagram size'
PREFERENCES_LABEL_LANGUAGE = 'Language'
PREFERENCES_TAB_EDITOR = 'Editor'
PREFERENCES_TAB_GENERAL = 'General'
PREFERENCES_WINDOW_TITLE = 'Preferences'

#############################################
# PROPERTIES DIALOG
#################################

PROPERTY_DIAGRAM_TAB_GENERAL = 'General'
PROPERTY_DIAGRAM_TAB_GEOMETRY = 'Geometry'
PROPERTY_DIAGRAM_LABEL_NUM_EDGES = 'N° edges'
PROPERTY_DIAGRAM_LABEL_NUM_NODES = 'N° nodes'
PROPERTY_DIAGRAM_LABEL_SIZE = 'Size'
PROPERTY_DIAGRAM_WINDOW_TITLE = 'Properties: {0}'

PROPERTY_NODE_LABEL_DATATYPE = 'Datatype'
PROPERTY_NODE_LABEL_DESCRIPTION = 'Description'
PROPERTY_NODE_LABEL_FACET = 'Facet'
PROPERTY_NODE_LABEL_HEIGHT = 'Height'
PROPERTY_NODE_LABEL_ID = 'ID'
PROPERTY_NODE_LABEL_IDENTITY = 'Identity'
PROPERTY_NODE_LABEL_NEIGHBOURS = 'Neighbours'
PROPERTY_NODE_LABEL_REFACTOR = 'Refactor'
PROPERTY_NODE_LABEL_SORT = 'Sort'
PROPERTY_NODE_LABEL_TEXT = 'Text'
PROPERTY_NODE_LABEL_TYPE = 'Type'
PROPERTY_NODE_LABEL_URL = 'URL'
PROPERTY_NODE_LABEL_WIDTH = 'Width'
PROPERTY_NODE_LABEL_VALUE = 'Value'
PROPERTY_NODE_LABEL_X = 'X'
PROPERTY_NODE_LABEL_Y = 'Y'
PROPERTY_NODE_WINDOW_TITLE = 'Properties: {0}'

PROPERTY_NODE_TAB_GENERAL = 'General'
PROPERTY_NODE_TAB_GEOMETRY = 'Geometry'
PROPERTY_NODE_TAB_LABEL = 'Label'
PROPERTY_NODE_TAB_ORDERING = 'Ordering'
PROPERTY_NODE_TAB_FACET = 'Facet'
PROPERTY_NODE_TAB_DATATYPE = 'Datatype'
PROPERTY_NODE_TAB_VALUE = 'Value'

#############################################
# REFACTOR NAME DIALOG
#################################

REFACTOR_NAME_RENAME_LABEL = 'Name'
REFACTOR_NAME_WINDOW_TITLE = 'Rename'
REFACTOR_NAME_CAPTION_NAME_NOT_VALID = "\'{0}\' is not a valid predicate name"

#############################################
# SYNTAX VALIDATION
#################################

SYNTAX_SELF_CONNECTION = 'Self connection is not valid'

SYNTAX_EQUIVALENCE_COMPLEMENT_NOT_VALID = '{0} equivalence is forbidden when expressing disjointness'

SYNTAX_INCLUSION_CHAIN_AS_TARGET = 'Role chain nodes cannot be target of a Role inclusion'
SYNTAX_INCLUSION_CHAIN_AS_SOURCE_INVALID_TARGET = 'Inclusion between {0} and {0} is forbidden'
SYNTAX_INCLUSION_COMPLEMENT_INVALID_SOURCE = 'Invalid source for {0} inclusion: {1}'
SYNTAX_INCLUSION_NO_GRAPHOL_EXPRESSION = 'Type mismatch: inclusion must involve two graphol expressions'
SYNTAX_INCLUSION_NOT_COMPATIBLE = 'Type mismatch: {0} and {1} are not compatible'
SYNTAX_INCLUSION_TYPE_MISMATCH = 'Type mismatch: inclusion between {0} and {1}'
SYNTAX_INCLUSION_VALUE_DOMAIN_EXPRESSIONS = 'Type mismatch: inclusion between value-domain expressions'

SYNTAX_INPUT_COMPLEMENT_INVALID_EXPRESSION = 'Invalid negative {0} expression'
SYNTAX_INPUT_DATA_TOO_MANY_DATATYPE = 'Too many value-domain nodes in input to datatype restriction node'
SYNTAX_INPUT_DATA_INVALID_FACET = 'Type mismatch: facet {0} is not supported by {1} datatype'
SYNTAX_INPUT_DR_INVALID_QUALIFIED_RESTRICTION = 'Invalid restriction ({0}) for qualified restriction'
SYNTAX_INPUT_DR_INVALID_QUALIFIED_RESTRICTION_OPERANDS = 'Invalid inputs ({0} + {1}) for qualified restriction'
SYNTAX_INPUT_DR_ATTRIBUTE_NO_SELF = 'Attributes do not have self'
SYNTAX_INPUT_ENUMERATION_INVALID_TARGET_IDENTITY = 'Target node has an invalid identity: {0}'
SYNTAX_INPUT_PROP_ASSERTION_TOO_MANY_INSTANCES = 'Too many instances in input to {0}'
SYNTAX_INPUT_PROP_ASSERTION_TOO_MANY_VALUES = 'Too many values in input to {0}'
SYNTAX_INPUT_INVALID_COMPOSITION = 'Type mismatch: {0} between {1} and {2}'
SYNTAX_INPUT_INVALID_OPERAND = 'Invalid input to {0}: {1}'
SYNTAX_INPUT_INVALID_TARGET = 'Input edges can only target constructor nodes'
SYNTAX_INPUT_TOO_MANY_OPERANDS = 'Too many inputs to {0}'

SYNTAX_MEMBERSHIP_INVALID_ASSERTION_TARGET = 'Invalid target for {0} assertion: {1}'
SYNTAX_MEMBERSHIP_INVALID_SOURCE = 'Invalid source for membership edge: {0}'
SYNTAX_MEMBERSHIP_INVALID_TARGET = 'Invalid target for membership edge: {0}'

SYNTAX_MANUAL_EDGE_ERROR = 'Syntax error detected on {0} from {1} to {2}: <i>{3}</i>.'
SYNTAX_MANUAL_NODE_IDENTITY_UNKNOWN = 'Unkown node identity detected on {0}.'
SYNTAX_MANUAL_NO_ERROR_FOUND = 'No syntax error found!'
SYNTAX_MANUAL_PROGRESS_TITLE = 'Running syntax validation...'
SYNTAX_MANUAL_WINDOW_TITLE = 'Syntax validation completed!'

#############################################
# TOOLBARS
#################################

TOOLBAR_DOCUMENT = 'Document'
TOOLBAR_EDITOR = 'Editor'
TOOLBAR_VIEW = 'View'
TOOLBAR_GRAPHOL = 'Graphol'

#############################################
# WELCOME SCREEN
#################################

WELCOME_ACTION_BUG_REPORT = 'Report a bug'
WELCOME_ACTION_VISIT_EDDY_HOME = 'GitHub repository'
WELCOME_ACTION_VISIT_GRAPHOL_WEBSITE = 'Visit Graphol website'
WELCOME_APP_VERSION = 'Version: {0}'
WELCOME_BTN_HELP = 'Help'
WELCOME_BTN_NEW_PROJECT = 'Create new project'
WELCOME_BTN_OPEN_PROJECT = 'Open project'
WELCOME_WINDOW_TITLE = 'Welcome to {0}'

#############################################
# WORKSPACE_DIALOG
#################################

WORKSPACE_CREATION_FAILED_WINDOW_TITLE = 'Workspace setup failed!'
WORKSPACE_CREATION_FAILED_MESSAGE = 'Eddy could not create the specified workspace: {0}!'
WORKSPACE_EDIT_FIELD_PREFIX = 'Workspace'
WORKSPACE_WINDOW_TITLE = 'Configure workspace'
WORKSPACE_HEAD_TITLE = 'Select a workspace'
WORKSPACE_HEAD_DESCRIPTION = 'Eddy stores your projects in a directory called workspace.\n' \
                             'Please choose a workspace directory to use.'