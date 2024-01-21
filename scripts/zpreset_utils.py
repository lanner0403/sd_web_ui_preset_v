import gradio as gr
import modules.sd_samplers
import modules.scripts as scripts
from modules import shared
import json
import os
import shutil
from pprint import pprint
from modules.ui import gr_show
from collections import namedtuple
from pathlib import Path

#  *********     versioning     *****
repo = None
version_map = {
    'https://github.com/vladmandic/automatic':"vlads",
    None: "a1111"
    }
#Test for a1111 or vlads, vlad had the courtesy to set a variable
if hasattr(shared, "url"):
    repo = version_map[getattr(shared, "url")]
else:
    repo = "a1111"

try:
    import launch

    if not launch.is_installed("colorama"):
            launch.run_pip("install colorama")
except:
    pass

try:
    from colorama import just_fix_windows_console, Fore, Style
    just_fix_windows_console()
except:
    pass

update_flag = "preset_manager_update_check"

additional_config_source = "additional_components.json"
additional_config_target = "additional_configs.json"
presets_config_source = "preset_configuration.json"
presets_config_target = "presets.json"

file_path = scripts.basedir() # file_path is basedir
scripts_path = os.path.join(file_path, "scripts")
path_to_update_flag = os.path.join(scripts_path, update_flag)
is_update_available = False
if os.path.exists(path_to_update_flag):
    is_update_available = True
    source_path = os.path.join(file_path, presets_config_source)
    target_path = os.path.join(file_path, presets_config_target)
    if not os.path.exists(target_path):
        shutil.move(source_path, target_path)
        print(f"Created: {presets_config_target}")
    else:
        print(f"Not writing {presets_config_target}: config exists already")
    os.remove(path_to_update_flag)

class PresetManager(scripts.Script):

    BASEDIR = scripts.basedir()

    def update_component_name(self, preset, oldval, newval):
        if preset.get(oldval) is not None:
            preset[newval] = preset.pop(oldval)

    def update_config(self):
        """This is a as per need method that will change per need"""
        component_remap = {
            "Highres. fix": "Hires. fix",
            "Firstpass width": "Upscaler",
            "Firstpass height": "Upscale by",
            "Sampling Steps": "Sampling steps",
            "Hires. steps": "Hires steps"
            }
        
        if repo == "vlads":
            component_remap.update({
                "Hires. fix" : "Hires fix"
            })

        
        config = self.get_config(self.settings_file)
        for preset in config.values():
            for old_val, new_val in component_remap.items():
                self.update_component_name(preset, old_val, new_val)
                    
        #PresetManager.all_presets = config
        #self.save_config(self.settings_file, config)


    def __init__(self, *args, **kwargs):
        
        self.compinfo = namedtuple("CompInfo", ["component", "label", "elem_id", "kwargs"])

        #self.settings_file = "preset_configuration.json"
        self.settings_file = "presets.json"
        #self.additional_settings_file = "additional_components.json"
        self.additional_settings_file = "additional_configs.json"
        #self.additional_components_for_presets = self.get_config(self.additional_settings_file) #additionalComponents

        # Read saved settings
        PresetManager.all_presets = self.get_config(self.settings_file)
        PresetManager.size_presets = self.get_config(self.additional_settings_file)
        
        self.available_components = list(PresetManager.all_presets["Reset"].keys())
        self.available_size_components = list(PresetManager.size_presets["Width"].keys())
        
        if is_update_available:
            self.update_config()

        # components that pass through after_components
        self.all_components = []

        # Initialize
        self.component_map = {k: None for k in self.available_components}
        self.size_component_map = {k:None for k in self.available_size_components}
        #self.additional_components = [x for x in self.additional_components_map] # acts like available_components list for additional components

        # combine defaults and choices
        #self.component_map = {**self.component_map, **self.additional_components_map}
        #self.available_components = self.available_components + self.additional_components


    
    def fakeinit(self, *args, **kwargs):
        """
        __init__ workaround, since some data is not available during instantiation, such as is_img2img, filename, etc.
        This method is called from .show(), as that's the first method ScriptRunner calls after handing some state dat (is_txt2img, is_img2img2)
        """
        #self.elm_prfx = f"{'txt2img' if self.is_txt2img else 'img2img'}"
        self.elm_prfx = "preset-v"


        # UI elements
        # class level
        # NOTE: Would love to use one component rendered twice, but gradio does not allow rendering twice, so I need one per page
        if self.is_txt2img:
            # quick set tab
            PresetManager.txt2img_preset_dropdown = gr.Dropdown(
                label="Presets",
                choices=list(PresetManager.all_presets.keys()),
                render = False,
                elem_id=f"{self.elm_prfx}_preset_qs_dd"
            )
            #else:
            # quick set tab
            PresetManager.img2img_preset_dropdown = gr.Dropdown(
                label="Presets",
                choices=list(PresetManager.all_presets.keys()),
                render = False,
                elem_id=f"{self.elm_prfx}_preset_qs_dd"
            )
            # size ddl
            PresetManager.txt2img_size_dropdown = gr.Dropdown(
                label="Size",
                choices=list(PresetManager.size_presets.keys()),
                render = False,
                elem_id=f"{self.elm_prfx}_size_qs_dd"
            )


            #按鈕版
            PresetManager.txt2img_preset1_btn = gr.Button(
                value="快速",
                label="Preset1",
                variant="primary",
                render = False,
                elem_id=f"{self.elm_prfx}_Preset1_btn"
            )
            PresetManager.txt2img_preset2_btn = gr.Button(
                value="優質",
                label="Preset2",
                variant="primary",
                render = False,
                elem_id=f"{self.elm_prfx}_Preset2_btn"
            )
            PresetManager.txt2img_preset3_btn = gr.Button(
                value="極優",
                label="Preset3",
                variant="primary",
                render = False,
                elem_id=f"{self.elm_prfx}_Preset3_btn"
            )

            PresetManager.txt2img_size1_btn = gr.Button(
                value="寬",
                label="Size1",
                variant="primary",
                render = False,
                elem_id=f"{self.elm_prfx}_size1_btn"
            )
            PresetManager.txt2img_size2_btn = gr.Button(
                value="高",
                label="Size2",
                variant="primary",
                render = False,
                elem_id=f"{self.elm_prfx}_size2_btn"
            )
            PresetManager.txt2img_size3_btn = gr.Button(
                value="方",
                label="Size3",
                variant="primary",
                render = False,
                elem_id=f"{self.elm_prfx}_size3_btn"
            )
            PresetManager.txt2img_prompt_btn = gr.Button(
                value="隨機提詞",
                label="randomprompt",
                variant="primary",
                render = False,
                elem_id=f"{self.elm_prfx}_prompt_btn"
            )

        # instance level
        # quick set tab
        #self.stackable_check = gr.Checkbox(value=True, label="Stackable", elem_id=f"{self.elm_prfx}_stackable_check", render=False)
        #self.save_as = gr.Text(render=False, label="Quick Save", elem_id=f"{self.elm_prfx}_save_qs_txt")
        #self.save_button = gr.Button(value="Save", variant="secondary", render=False, visible=False, elem_id=f"{self.elm_prfx}_save_qs_bttn")

        self.hide_all_button = gr.Button(value="簡易版", variant="primary", render=False, visible=True, elem_id=f"{self.elm_prfx}_hide_all_bttn")
        self.show_all_button = gr.Button(value="一般版", variant="primary", render=False, visible=True, elem_id=f"{self.elm_prfx}_show_all_bttn")
        #self.random_button = gr.Button(value="隨機圖", variant="primary", render=False, visible=True, elem_id=f"{self.elm_prfx}_random_bttn")

    def title(self):
        return "Presets"

    def show(self, is_img2img):
        self.fakeinit()
        return True
        if self.ui_first == "sampler":
            if shared.opts.samplers_in_dropdown:
                self.before_component_label = "Sampling method"
            else:
                self.before_component_label = "Sampling Steps"
            return True
        else:
            self.before_component_label = self.positon_manager
            return True

    def before_component(self, component, **kwargs):
        pass
    def _before_component(self, component, **kwargs):
        # Define location of where to show up
        #if kwargs.get("elem_id") == "":#f"{'txt2img' if self.is_txt2img else 'img2img'}_progress_bar":
        #print(kwargs.get("label") == self.before_component_label, "TEST", kwargs.get("label"))
        #if kwargs.get("label") == self.before_component_label:
            with gr.Accordion(label="簡易設定", open = True, elem_id=f"{'txt2img' if self.is_txt2img else 'img2img'}_preset_manager_accordion"):
                #with gr.Row(equal_height = True):
                    #if self.is_txt2img:
                        #PresetManager.txt2img_preset_dropdown.render()
                    #else:
                        #PresetManager.img2img_preset_dropdown.render()
                with gr.Row(equal_height = True):
                    PresetManager.txt2img_preset1_btn.render()
                    PresetManager.txt2img_preset2_btn.render()
                    PresetManager.txt2img_preset3_btn.render()
                    #with gr.Column(elem_id=f"{self.elm_prfx}_ref_del_col_qs"):
                        #self.stackable_check.render()
                #with gr.Row(equal_height = True):
                    #PresetManager.txt2img_size_dropdown.render()
                with gr.Row(equal_height = True):
                    PresetManager.txt2img_size1_btn.render()
                    PresetManager.txt2img_size2_btn.render()
                    PresetManager.txt2img_size3_btn.render()
            with gr.Row(equal_height = True):
                self.hide_all_button.render()
                self.show_all_button.render()
            with gr.Row(equal_height = True):
                PresetManager.txt2img_prompt_btn.render()

    def after_component(self, component, **kwargs):
        if hasattr(component, "label") or hasattr(component, "elem_id"):
            self.all_components.append(self.compinfo(
                                                      component=component,
                                                      label=component.label if hasattr(component, "label") else None,
                                                      elem_id=component.elem_id if hasattr(component, "elem_id") else None,
                                                      kwargs=kwargs
                                                     )
                                      )
            #if hasattr(component, "label"):
                #print(f"label:{component.label}")
            #elif hasattr(component, "elem_id"):
                #print(f"elem_id:{component.elem_id}")

        label = kwargs.get("label")
        ele = kwargs.get("elem_id")
        # TODO: element id
        #if label in self.component_map or label in self.additional_components_map:# and ele == self.additional_components["additionalComponents"]) or (ele == self.additional_components["additionalComponents"]):
        if label in self.component_map:# and ele == self.additional_components["additionalComponents"]) or (ele == self.additional_components["additionalComponents"]):
            #!Hack to remove conflict between main Prompt and hr Prompt
            if self.component_map[label] is None:
                self.component_map.update({component.label: component})
        if label in self.size_component_map:
            if self.size_component_map[label] is None:
                self.size_component_map.update({component.label: component})
        # 提示詞
        if ele == "txt2img_prompt": 
            self.prompt_component = component

        if ele == "txt2img_generation_info_button" or ele == "img2img_generation_info_button":
            self._ui()

        if ele == "txt2img_styles_dialog":
            self._before_component("")
            

    def ui(self, *args):
        pass

    def _ui(self):
        # Conditional for class members
        if self.is_txt2img:
            # Quick Set Tab
            PresetManager.txt2img_preset_dropdown.change(
                fn=self.fetch_valid_values_from_preset,
                inputs=[PresetManager.txt2img_preset_dropdown] + [self.component_map[comp_name] for comp_name in list(x for x in self.available_components if self.component_map[x] is not None)],
                outputs=[self.component_map[comp_name] for comp_name in list(x for x in self.available_components if self.component_map[x] is not None)],
            )
            #PresetManager.txt2img_size_dropdown.change(
            #    fn=self.fetch_valid_values_from_size,
            #    inputs=[PresetManager.txt2img_size_dropdown] + [self.size_component_map[comp_name] for comp_name in list(x for x in self.available_size_components if self.size_component_map[x] is not None)],
            #    outputs=[self.size_component_map[comp_name] for comp_name in list(x for x in self.available_size_components if self.size_component_map[x] is not None)],
            #)
            PresetManager.txt2img_preset1_btn.click(
                fn=self.fetch_valid_values_from_preset1,
                outputs=[self.component_map[comp_name] for comp_name in list(x for x in self.available_components if self.component_map[x] is not None)],
            ) 
            PresetManager.txt2img_preset2_btn.click(
                fn=self.fetch_valid_values_from_preset2,
                outputs=[self.component_map[comp_name] for comp_name in list(x for x in self.available_components if self.component_map[x] is not None)],
            )    
            PresetManager.txt2img_preset3_btn.click(
                fn=self.fetch_valid_values_from_preset3,
                outputs=[self.component_map[comp_name] for comp_name in list(x for x in self.available_components if self.component_map[x] is not None)],
            )               
            PresetManager.txt2img_size1_btn.click(
                fn=self.fetch_valid_values_from_size1,
                outputs=[self.size_component_map[comp_name] for comp_name in list(x for x in self.available_size_components if self.size_component_map[x] is not None)],
            )
            PresetManager.txt2img_size2_btn.click(
                fn=self.fetch_valid_values_from_size2,
                outputs=[self.size_component_map[comp_name] for comp_name in list(x for x in self.available_size_components if self.size_component_map[x] is not None)],
            )
            PresetManager.txt2img_size3_btn.click(
                fn=self.fetch_valid_values_from_size3,
                outputs=[self.size_component_map[comp_name] for comp_name in list(x for x in self.available_size_components if self.size_component_map[x] is not None)],
            )
            PresetManager.txt2img_prompt_btn.click(
                fn=self.fetch_valid_values_from_prompt,
                outputs=self.prompt_component
            )
        else:
            # Quick Set Tab
            PresetManager.img2img_preset_dropdown.change(
                fn=self.fetch_valid_values_from_preset,
                inputs=[PresetManager.img2img_preset_dropdown] + [self.component_map[comp_name] for comp_name in list(x for x in self.available_components if self.component_map[x] is not None)],
                outputs=[self.component_map[comp_name] for comp_name in list(x for x in self.available_components if self.component_map[x] is not None)],
            )

    def f_b_syncer(self):
        """
        ?Front/Backend synchronizer?
        Not knowing what else to call it, simple idea, rough to figure out. When updating choices on the front-end, back-end isn't updated, make them both match
        https://github.com/gradio-app/gradio/discussions/2848
        """
        self.inspect_dd.choices = [str(x) for x in self.all_components]
        return [gr.update(choices=[str(x) for x in self.all_components]), gr.Button.update(visible=False)]

    
    def inspection_formatter(self, x):
        comp = self.all_components[x]
        text = f"Component Label: {comp.label}\nElement ID: {comp.elem_id}\nComponent: {comp.component}\nAll Info Handed Down: {comp.kwargs}"
        return text


    def run(self, p, *args):
        pass

    def get_config(self, path, open_mode='r'):
        file = os.path.join(PresetManager.BASEDIR, path)
        try:
            with open(file, open_mode) as f:
                as_dict = json.load(f) 
        except FileNotFoundError as e:
            print(f"{e}\n{file} not found, check if it exists or if you have moved it.")
        return as_dict 
    

    def fetch_valid_values_from_preset(self, selection, *comps_vals):
        print(selection)
        print(comps_vals)
        return [
            PresetManager.all_presets[selection][comp_name] 
                if (comp_name in PresetManager.all_presets[selection] 
                    and (
                        True if not hasattr(self.component_map[comp_name], "choices") 
                            else 
                            True if PresetManager.all_presets[selection][comp_name] in self.component_map[comp_name].choices 
                                else False 
                        ) 
                    ) 
                else 
                    self.component_map[comp_name].value
                for i, comp_name in enumerate(list(x for x in self.available_components if self.component_map[x] is not None and hasattr(self.component_map[x], "value")))]
    
    def fetch_valid_values_from_size(self, selection, *comps_vals):
        print(selection)
        print(comps_vals)
        return [
            PresetManager.size_presets[selection][comp_name] 
                if (comp_name in PresetManager.size_presets[selection] 
                    and (
                        True if not hasattr(self.size_component_map[comp_name], "choices") 
                            else 
                            True if PresetManager.size_presets[selection][comp_name] in self.size_component_map[comp_name].choices 
                                else False 
                        ) 
                    ) 
                else 
                    self.size_component_map[comp_name].value
                for i, comp_name in enumerate(list(x for x in self.available_size_components if self.size_component_map[x] is not None and hasattr(self.size_component_map[x], "value")))]
    
    #按鈕版
    def fetch_valid_values_from_preset1(self):
        return [
            PresetManager.all_presets["Quick"][comp_name] 
                if (comp_name in PresetManager.all_presets["Quick"] 
                    and (
                        True if not hasattr(self.component_map[comp_name], "choices") 
                            else 
                            True if PresetManager.all_presets["Quick"][comp_name] in self.component_map[comp_name].choices 
                                else False 
                        ) 
                    ) 
                else 
                    self.component_map[comp_name].value
                for i, comp_name in enumerate(list(x for x in self.available_components if self.component_map[x] is not None and hasattr(self.component_map[x], "value")))]
    
    def fetch_valid_values_from_preset2(self):
        return [
            PresetManager.all_presets["Better"][comp_name] 
                if (comp_name in PresetManager.all_presets["Better"] 
                    and (
                        True if not hasattr(self.component_map[comp_name], "choices") 
                            else 
                            True if PresetManager.all_presets["Better"][comp_name] in self.component_map[comp_name].choices 
                                else False 
                        ) 
                    ) 
                else 
                    self.component_map[comp_name].value
                for i, comp_name in enumerate(list(x for x in self.available_components if self.component_map[x] is not None and hasattr(self.component_map[x], "value")))]
    
    def fetch_valid_values_from_preset3(self):
        return [
            PresetManager.all_presets["Great"][comp_name] 
                if (comp_name in PresetManager.all_presets["Great"] 
                    and (
                        True if not hasattr(self.component_map[comp_name], "choices") 
                            else 
                            True if PresetManager.all_presets["Great"][comp_name] in self.component_map[comp_name].choices 
                                else False 
                        ) 
                    ) 
                else 
                    self.component_map[comp_name].value
                for i, comp_name in enumerate(list(x for x in self.available_components if self.component_map[x] is not None and hasattr(self.component_map[x], "value")))]
    
    def fetch_valid_values_from_size1(self):
        return [
            PresetManager.size_presets["Width"][comp_name] 
                if (comp_name in PresetManager.size_presets["Width"] 
                    and (
                        True if not hasattr(self.size_component_map[comp_name], "choices") 
                            else 
                            True if PresetManager.size_presets["Width"][comp_name] in self.size_component_map[comp_name].choices 
                                else False 
                        ) 
                    ) 
                else 
                    self.size_component_map[comp_name].value
                for i, comp_name in enumerate(list(x for x in self.available_size_components if self.size_component_map[x] is not None and hasattr(self.size_component_map[x], "value")))]
    
    def fetch_valid_values_from_size2(self):
        return [
            PresetManager.size_presets["Height"][comp_name] 
                if (comp_name in PresetManager.size_presets["Height"] 
                    and (
                        True if not hasattr(self.size_component_map[comp_name], "choices") 
                            else 
                            True if PresetManager.size_presets["Height"][comp_name] in self.size_component_map[comp_name].choices 
                                else False 
                        ) 
                    ) 
                else 
                    self.size_component_map[comp_name].value
                for i, comp_name in enumerate(list(x for x in self.available_size_components if self.size_component_map[x] is not None and hasattr(self.size_component_map[x], "value")))]
    
    def fetch_valid_values_from_size3(self):
        return [
            PresetManager.size_presets["Square"][comp_name] 
                if (comp_name in PresetManager.size_presets["Square"] 
                    and (
                        True if not hasattr(self.size_component_map[comp_name], "choices") 
                            else 
                            True if PresetManager.size_presets["Square"][comp_name] in self.size_component_map[comp_name].choices 
                                else False 
                        ) 
                    ) 
                else 
                    self.size_component_map[comp_name].value
                for i, comp_name in enumerate(list(x for x in self.available_size_components if self.size_component_map[x] is not None and hasattr(self.size_component_map[x], "value")))]
    
    def fetch_valid_values_from_prompt(self):
        self.prompt_component.value = "nsfw++++,"
        return self.prompt_component.value
 

    def local_request_restart(self):
        "Restart button"
        shared.state.interrupt()
        shared.state.need_restart = True

