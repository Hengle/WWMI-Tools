import bpy
import json

from textwrap import dedent


class WWMI_TOOLS_PT_SidePanelIniToggles(bpy.types.Panel):
    bl_label = "Ini Toggles"
    bl_idname = "WWMI_TOOLS_PT_INI_TOGGLES"
    bl_parent_id = "WWMI_TOOLS_PT_SIDEBAR"
    bl_options = {'DEFAULT_CLOSED'}
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "WWMI Tools"
    bl_order = 81

    @classmethod
    def poll(cls, context):
        cfg = context.scene.wwmi_tools_settings
        return cfg.tool_mode == 'EXPORT_MOD'
    
    def draw(self, context):
        layout = self.layout
        cfg = context.scene.wwmi_tools_settings
    
        layout.prop(cfg, 'use_ini_toggles')
        
        layout.operator("wwmi_tools.open_ini_toggles_import_export_editor")

        layout.prop(cfg.ini_toggles, 'hide_empty_states')
        layout.prop(cfg.ini_toggles, 'hide_default_conditions')

        row = layout.row()
        row.operator("wwmi_tools.collapse_toggle_vars", icon="TRIA_DOWN")
        row.operator("wwmi_tools.expand_toggle_vars", icon="TRIA_RIGHT")

        layout.operator("wwmi_tools.add_toggle_var", text="Add Var", icon="ADD")

        for i in reversed(range(len(cfg.ini_toggles.vars))):
            var = cfg.ini_toggles.vars[i]

            box = layout.box()

            row = box.row()

            row.prop(var, "ui_expanded", icon="TRIA_DOWN" if var.ui_expanded else "TRIA_RIGHT", emboss=False, text="")

            hotkeys = " ".join([f"[{binding}]" for binding in var.get_formatted_hotkeys(join_arg='+')])

            if var.ui_expanded:
                split = row.split(factor=0.7)
                split.prop(var, "name", text="")
                split.label(text=hotkeys)
            else:
                row.label(text=f'{var.name} {hotkeys}')

            if var.ui_expanded:
                op = row.operator("wwmi_tools.add_var_state", text="", icon="ADD")
                op.var_index = i

            op = row.operator("wwmi_tools.edit_toggle_var", text="", icon="PREFERENCES")
            op.var_index = i
            if not var.ui_expanded:
                op = row.operator("wwmi_tools.move_toggle_var", icon='TRIA_UP', text="")
                op.var_index = i
                op.direction = 'UP'
                op = row.operator("wwmi_tools.move_toggle_var", icon='TRIA_DOWN', text="")
                op.var_index = i
                op.direction = 'DOWN'
            op = row.operator("wwmi_tools.remove_toggle_var", text="", icon="X")
            op.var_index = i

            if var.ui_expanded:

                for j, state in enumerate(var.states):
                    if state.name == "-1" and cfg.ini_toggles.hide_empty_states and len(state.objects) == 0:
                        continue

                    sub_box = box.box()
                    sub_row = sub_box.row()

                    if var.default_state == state.name:
                        sub_row.label(text=f"State {state.name} (default)")
                    else:
                        sub_row.label(text=f"State {state.name}")

                    op = sub_row.operator("wwmi_tools.add_var_state_object", text="", icon="ADD")
                    op.var_index = i
                    op.state_index = j
                    
                    op = sub_row.operator("wwmi_tools.move_toggle_var_state", icon='TRIA_UP', text="")
                    op.var_index = i
                    op.state_index = j
                    op.direction = 'UP'
                    op = sub_row.operator("wwmi_tools.move_toggle_var_state", icon='TRIA_DOWN', text="")
                    op.var_index = i
                    op.state_index = j
                    op.direction = 'DOWN'

                    if state.name == "-1":      
                        sub_row = sub_row.row()
                        sub_row.enabled = False 

                    op = sub_row.operator("wwmi_tools.remove_var_state", text="", icon="X")
                    op.var_index = i
                    op.state_index = j

                    for k, obj_item in enumerate(state.objects):
                        obj_row = sub_box.row()

                        if len(obj_item.conditions) > 0:
                            condition = obj_item.conditions[0]
                            is_custom_condition = condition.var != var.name or condition.state != state.name or condition.operator != '=='
                            if not cfg.ini_toggles.hide_default_conditions or is_custom_condition:
                                obj_row.label(text='if ' + obj_item.format_conditions())
                                obj_row = sub_box.row()

                        obj_row.prop(obj_item, "object", text="")
                                            
                        op = obj_row.operator("wwmi_tools.edit_var_state_object", text="", icon="PREFERENCES")
                        op.var_index = i
                        op.state_index = j
                        op.object_index = k
                        
                        op = obj_row.operator("wwmi_tools.remove_var_state_object", text="", icon="X")
                        op.var_index = i
                        op.state_index = j
                        op.object_index = k


class WWMI_TOOLS_OT_CollapseToggleVars(bpy.types.Operator):
    bl_idname = "wwmi_tools.collapse_toggle_vars"
    bl_label = "Collapse Vars"
    bl_description = "Fold all vars in the list (exit edit mode for each var)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cfg = context.scene.wwmi_tools_settings
        for var in cfg.ini_toggles.vars:
            var.ui_expanded = False
        return {'FINISHED'}
    

class WWMI_TOOLS_OT_ExpandToggleVars(bpy.types.Operator):
    bl_idname = "wwmi_tools.expand_toggle_vars"
    bl_label = "Expand Vars"
    bl_description = "Fold all vars in the list (enter edit mode for each var)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cfg = context.scene.wwmi_tools_settings
        for var in cfg.ini_toggles.vars:
            var.ui_expanded = True
        return {'FINISHED'}


class WWMI_TOOLS_OT_AddToggleVar(bpy.types.Operator):
    bl_idname = "wwmi_tools.add_toggle_var"
    bl_label = "Add Toggle Var"
    bl_description = "Add new var to Ini Toggles, it will be used in mod.ini to control visibility of Objects listed in its States"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cfg = context.scene.wwmi_tools_settings
        cfg.ini_toggles.add_new_var()
        return {'FINISHED'}


class WWMI_TOOLS_OT_RemoveToggleVar(bpy.types.Operator):
    bl_idname = "wwmi_tools.remove_toggle_var"
    bl_label = "Remove Toggle Var"
    bl_description = "Remove var from Ini Toggles"
    bl_options = {'REGISTER', 'UNDO'}

    var_index: bpy.props.IntProperty()  # type: ignore

    def execute(self, context):
        cfg = context.scene.wwmi_tools_settings
        cfg.ini_toggles.vars.remove(self.var_index)
        return {'FINISHED'}


class WWMI_TOOLS_OT_MoveToggleVar(bpy.types.Operator):
    bl_idname = "wwmi_tools.move_toggle_var"
    bl_label = "Move Toggle Var"
    bl_description = "Move var in Ini Toggles list"
    bl_options = {'REGISTER', 'UNDO'}
    
    var_index: bpy.props.IntProperty()  # type: ignore
    direction: bpy.props.EnumProperty(items=[('UP', "Up", ""), ('DOWN', "Down", "")])  # type: ignore

    def execute(self, context):
        cfg = context.scene.wwmi_tools_settings

        if self.direction == 'UP':
            new_idx = self.var_index - 1
        else:
            new_idx = self.var_index + 1

        if new_idx < 0 or new_idx >= len(cfg.ini_toggles.vars):
            return {'CANCELLED'}

        cfg.ini_toggles.vars.move(self.var_index, new_idx)
        return {'FINISHED'}



class WWMI_TOOLS_OT_EditToggleVar(bpy.types.Operator):
    bl_idname = "wwmi_tools.edit_toggle_var"
    bl_label = "Edit Var"
    bl_description = "Configure var hotkey and default state"
    bl_options = {'REGISTER', 'UNDO'}

    var_index: bpy.props.IntProperty()  # type: ignore

    def draw(self, context):
        cfg = context.scene.wwmi_tools_settings
        layout = self.layout
        
        layout.label(text="Toggle Var Settings:")

        var = cfg.ini_toggles.vars[self.var_index]

        box = layout.box()
        
        row = box.row()
        
        split = row.split(factor=0.7)
        
        split.prop(var, "hotkeys")

        op = split.operator("wm.url_open", text="Key Codes", icon='HELP')
        op.url = "https://learn.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes"

        row = box.row()
        row.prop_search(var, "default_state", var, "states")

        row = box.row()
        row.prop(var, "hide_empty_state")

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=350)

    def execute(self, context):
        return {'FINISHED'}
    

class WWMI_TOOLS_OT_AddToggleVarState(bpy.types.Operator):
    bl_idname = "wwmi_tools.add_var_state"
    bl_label = "Add State"
    bl_description = "Add new state to the var, each state may control visibility of multiple objects"
    bl_options = {'REGISTER', 'UNDO'}

    var_index: bpy.props.IntProperty()  # type: ignore

    def execute(self, context):
        cfg = context.scene.wwmi_tools_settings
        var = cfg.ini_toggles.vars[self.var_index]
        var.add_new_state()
        return {'FINISHED'}


class WWMI_TOOLS_OT_RemoveToggleVarState(bpy.types.Operator):
    bl_idname = "wwmi_tools.remove_var_state"
    bl_label = "Remove State"
    bl_description = "Remove this state from Ini Toggles Var"
    bl_options = {'REGISTER', 'UNDO'}

    var_index: bpy.props.IntProperty()  # type: ignore
    state_index: bpy.props.IntProperty()  # type: ignore

    def execute(self, context):
        cfg = context.scene.wwmi_tools_settings
        var = cfg.ini_toggles.vars[self.var_index]
        var.remove_state(self.state_index)
        return {'FINISHED'}


class WWMI_TOOLS_OT_MoveToggleVarState(bpy.types.Operator):
    bl_idname = "wwmi_tools.move_toggle_var_state"
    bl_label = "Move Toggle Var State"
    bl_description = "Move var state in the list"
    bl_options = {'REGISTER', 'UNDO'}
    
    var_index: bpy.props.IntProperty()  # type: ignore
    state_index: bpy.props.IntProperty()  # type: ignore
    direction: bpy.props.EnumProperty(items=[('UP', "Up", ""), ('DOWN', "Down", "")])  # type: ignore

    def execute(self, context):
        cfg = context.scene.wwmi_tools_settings
        var = cfg.ini_toggles.vars[self.var_index]

        if self.direction == 'UP':
            new_idx = self.state_index - 1
        else:
            new_idx = self.state_index + 1

        if new_idx < 0 or new_idx >= len(var.states):
            return {'CANCELLED'}

        var.swap_states(self.state_index, new_idx)

        return {'FINISHED'}


class WWMI_TOOLS_OT_AddToggleVarStateObject(bpy.types.Operator):
    bl_idname = "wwmi_tools.add_var_state_object"
    bl_label = "Add object to state to make it conditionally visible"
    bl_options = {'REGISTER', 'UNDO'}

    var_index: bpy.props.IntProperty()  # type: ignore
    state_index: bpy.props.IntProperty()  # type: ignore

    def execute(self, context):
        cfg = context.scene.wwmi_tools_settings
        var = cfg.ini_toggles.vars[self.var_index]
        state = var.states[self.state_index]
        state.add_new_state_object(var.name)
        return {'FINISHED'}


class WWMI_TOOLS_OT_RemoveToggleVarStateObject(bpy.types.Operator):
    bl_idname = "wwmi_tools.remove_var_state_object"
    bl_label = "Remove State Object"
    bl_description = "Remove this object from the state"
    bl_options = {'REGISTER', 'UNDO'}

    var_index: bpy.props.IntProperty()  # type: ignore
    state_index: bpy.props.IntProperty()  # type: ignore
    object_index: bpy.props.IntProperty()  # type: ignore

    def execute(self, context):
        cfg = context.scene.wwmi_tools_settings
        group = cfg.ini_toggles.vars[self.var_index]
        state = group.states[self.state_index]
        state.objects.remove(self.object_index)
        return {'FINISHED'}


class WWMI_TOOLS_OT_EditVarStateObject(bpy.types.Operator):
    bl_idname = "wwmi_tools.edit_var_state_object"
    bl_label = "Edit Conditions"
    bl_description = "Open configuration window for custom conditions"

    var_index: bpy.props.IntProperty()  # type: ignore
    state_index: bpy.props.IntProperty()  # type: ignore
    object_index: bpy.props.IntProperty()  # type: ignore

    def draw(self, context):
        cfg = context.scene.wwmi_tools_settings
        layout = self.layout
        
        layout.label(text="State Object Conditions:")

        var = cfg.ini_toggles.vars[self.var_index]
        state = var.states[self.state_index]
        obj = state.objects[self.object_index]

        for i, condition in enumerate(obj.conditions):
            box = layout.box()
            
            row = box.row()

            split = row.split(factor=0.1)

            split.prop(condition, "logic", text="")
            
            split = split.split(factor=0.2)

            split.prop(condition, "type", text="")

            split = split.split(factor=0.5)

            if condition.type == 'TOGGLE':
                split.prop_search(condition, "var", cfg.ini_toggles, "vars", text="")
            else:
                split.prop(condition, "var", text="")

            split = split.split(factor=0.3)

            split.prop(condition, "operator", text="")
            
            split = split.split(factor=0.8)

            if condition.type == 'TOGGLE':
                cond_group = cfg.ini_toggles.vars.get(condition.var, None)
                if cond_group is not None:
                    split.prop_search(condition, "state", cond_group, "states", text="")
                else:
                    split.label(text="N/A")
            else:
                split.prop(condition, "state", text="")

            remove_op = split.operator("wwmi_tools.remove_condition", text="", icon='X')
            remove_op.var_index = self.var_index
            remove_op.state_index = self.state_index
            remove_op.object_index = self.object_index
            remove_op.condition_index = i

        add_op = layout.operator("wwmi_tools.add_condition")
        add_op.var_index = self.var_index
        add_op.state_index = self.state_index
        add_op.object_index = self.object_index

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=500)

    def execute(self, context):
        return {'FINISHED'}
    

class WWMI_TOOLS_OT_AddToggleVarStateObjectCondition(bpy.types.Operator):
    bl_idname = "wwmi_tools.add_condition"
    bl_label = "Add Condition"
    bl_options = {'REGISTER', 'UNDO'}

    var_index: bpy.props.IntProperty() # type: ignore
    state_index: bpy.props.IntProperty() # type: ignore
    object_index: bpy.props.IntProperty() # type: ignore

    def execute(self, context):
        cfg = context.scene.wwmi_tools_settings
        obj = cfg.ini_toggles.vars[self.var_index].states[self.state_index].objects[self.object_index]
        obj.conditions.add()
        return {'FINISHED'}


class WWMI_TOOLS_OT_RemoveToggleVarStateObjectCondition(bpy.types.Operator):
    bl_idname = "wwmi_tools.remove_condition"
    bl_label = "Remove Condition"
    bl_options = {'REGISTER', 'UNDO'}

    var_index: bpy.props.IntProperty() # type: ignore
    state_index: bpy.props.IntProperty() # type: ignore
    object_index: bpy.props.IntProperty() # type: ignore
    condition_index: bpy.props.IntProperty() # type: ignore

    def execute(self, context):
        cfg = context.scene.wwmi_tools_settings
        obj = cfg.ini_toggles.vars[self.var_index].states[self.state_index].objects[self.object_index]
        if self.condition_index < len(obj.conditions):
            obj.conditions.remove(self.condition_index)
        return {'FINISHED'}


class WWMI_TOOLS_OpenIniTogglesImportExportEditor(bpy.types.Operator):
    bl_idname = "wwmi_tools.open_ini_toggles_import_export_editor"
    bl_label = "Open Ini Toggles Import Export"
    bl_description = "Open text editor window for Ini Toggles Vars import or export"

    def execute(self, context):
        cfg = context.scene.wwmi_tools_settings

        text_name = "IniTogglesImportExportText"

        if text_name in bpy.data.texts:
            text = bpy.data.texts[text_name]
        else:
            text = bpy.data.texts.new(text_name)
        
        text.clear()
        text.write(dedent("""
            This tool allows to backup your toggles or copy them to another project aka .blend file

            To "[Import]" Ini Toggles Vars:
            1. Create new text via button on the middle panel above (or clear this text)
            2. Paste Ini Toggles export text
            3. Press "Import Ini Toggles" on side panel "Ini Toggles - WWMI Tools" to the right

            To "[Export]" Ini Toggles Vars:
            1. Press "Export Ini Toggles" on side panel "Ini Toggles - WWMI Tools" to the right
            2. Copy generated export text
        """))
        text.cursor_set(0)

        new_window = bpy.ops.wm.window_new()
        
        new_window_context = bpy.context.window_manager.windows[-1]

        # Switch the area to TEXT_EDITOR and assign the text
        for area in new_window_context.screen.areas:
            area.type = 'TEXT_EDITOR'
            text_area = area
            for space in area.spaces:
                if space.type == 'TEXT_EDITOR':
                    space.text = text

        # Toggle Tools sidebar
        if text_area:
            for region in text_area.regions:
                if region.type == 'UI':
                    bpy.ops.wm.context_toggle(data_path="space_data.show_region_ui")
                    break
        
        return {'FINISHED'}


class WWMI_TOOLS_ExportIniToggles(bpy.types.Operator):
    bl_idname = "wwmi_tools.export_ini_toggles"
    bl_label = "Export Ini Toggles"
    bl_description = "Output Ini Toggles Vars as importable .json text to IniTogglesExportText file of this Text Editor"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cfg = context.scene.wwmi_tools_settings
        
        text_name = "IniTogglesExportText"

        if text_name in bpy.data.texts:
            text = bpy.data.texts[text_name]
        else:
            text = bpy.data.texts.new(text_name)
        
        text.clear()
        text.write(json.dumps(cfg.ini_toggles.export_vars(), indent=4))
        text.cursor_set(0)

        # Switch the area to TEXT_EDITOR and assign the text
        for area in context.screen.areas:
            area.type = 'TEXT_EDITOR'
            for space in area.spaces:
                if space.type == 'TEXT_EDITOR':
                    space.text = text

        return {'FINISHED'}


class WWMI_TOOLS_ImportIniToggles(bpy.types.Operator):
    bl_idname = "wwmi_tools.import_ini_toggles"
    bl_label = "Import Ini Toggles"
    bl_description = "Import Ini Toggles Vars from .json text of current file"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cfg = context.scene.wwmi_tools_settings
        
        text = None
        for area in context.screen.areas:
            if area.type == 'TEXT_EDITOR':
                for space in area.spaces:
                    if space.type == 'TEXT_EDITOR' and space.text:
                        text = space.text
                        break
        try:
            if text is None:
                raise ValueError(f'Text editor area has no text file open!')
            try:
                data = json.loads(text.as_string())
            except Exception as e:
                raise ValueError(f'Unknown data format (not a json dict)') from e
            imported_vars_count, skipped_vars_count = cfg.ini_toggles.import_vars(
                data, cfg.ini_toggles.replace_vars_on_import, cfg.ini_toggles.clear_vars_on_import
            )
            msg = f'Imported {imported_vars_count} Ini Toggle Vars'
            if skipped_vars_count > 0:
                msg += f' (skipped {skipped_vars_count} duplicates)'
            self.report({'INFO'}, msg)
        except Exception as e:
            self.report({'ERROR'}, f'Failed to import Ini Toggle Vars: {e}')
            # Roll back the operator's changes
            bpy.ops.ed.undo()
            return {'CANCELLED'}

        return {'FINISHED'}
    

class WWMI_TOOLS_PT_TEXT_EDITOR_IniToggles(bpy.types.Panel):
    bl_label = "Ini Toggles - WWMI Tools"
    bl_space_type = "TEXT_EDITOR"
    bl_region_type = "UI"
    bl_category = "Text"

    def draw(self, context):
        layout = self.layout
        cfg = context.scene.wwmi_tools_settings
        layout.operator(WWMI_TOOLS_ExportIniToggles.bl_idname)
        layout.operator(WWMI_TOOLS_ImportIniToggles.bl_idname)
        layout.prop(cfg.ini_toggles, 'replace_vars_on_import')
        layout.prop(cfg.ini_toggles, 'clear_vars_on_import')
