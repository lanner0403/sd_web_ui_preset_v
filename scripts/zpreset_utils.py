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
    try:
        print(Fore.CYAN + "Thank you for using:" + Fore.GREEN + "https://github.com/Gerschel/sd_web_ui_preset_utils/")
        print(Fore.RED +"""
______                   _    ___  ___                                  
| ___ \                 | |   |  \/  |                                  
| |_/ / __ ___  ___  ___| |_  | .  . | __ _ _ __   __ _  __ _  ___ _ __ 
|  __/ '__/ _ \/ __|/ _ \ __| | |\/| |/ _` | '_ \ / _` |/ _` |/ _ \ '__|
| |  | | |  __/\__ \  __/ |_  | |  | | (_| | | | | (_| | (_| |  __/ |   
\_|  |_|  \___||___/\___|\__| \_|  |_/\__,_|_| |_|\__,_|\__, |\___|_|   
                                                         __/ |          
                                                        |___/           
""")
        print(Fore.YELLOW + "By: Gerschel Payne")
        print(Style.RESET_ALL + "Preset Manager: Checking for pre-existing configuration files.")
    except NameError:
        print( "Thank you for using: https://github.com/Gerschel/sd_web_ui_preset_utils/")
        print("""
______                   _    ___  ___                                  
| ___ \                 | |   |  \/  |                                  
| |_/ / __ ___  ___  ___| |_  | .  . | __ _ _ __   __ _  __ _  ___ _ __ 
|  __/ '__/ _ \/ __|/ _ \ __| | |\/| |/ _` | '_ \ / _` |/ _` |/ _ \ '__|
| |  | | |  __/\__ \  __/ |_  | |  | | (_| | | | | (_| | (_| |  __/ |   
\_|  |_|  \___||___/\___|\__| \_|  |_/\__,_|_| |_|\__,_|\__, |\___|_|   
                                                         __/ |          
                                                        |___/           
""")
        print("By: Gerschel Payne")
        print("Preset Manager: Checking for pre-existing configuration files.")


    source_path = os.path.join(file_path, additional_config_source)
    target_path = os.path.join(file_path, additional_config_target)
    if not os.path.exists(target_path):
        shutil.move(source_path, target_path)
        print(f"Created: {additional_config_target}")
    else:
        print(f"Not writing {additional_config_target}: config exists already")
                    
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
        self.save_config(self.settings_file, config)


    def __init__(self, *args, **kwargs):
        
        self.compinfo = namedtuple("CompInfo", ["component", "label", "elem_id", "kwargs"])

        #self.settings_file = "preset_configuration.json"
        self.settings_file = "presets.json"
        #self.additional_settings_file = "additional_components.json"
        self.additional_settings_file = "additional_configs.json"


        self.additional_components_for_presets = self.get_config(self.additional_settings_file) #additionalComponents
        self.available_components = [
	    "Stable Diffusion checkpoint",
            "Prompt", #! must create filter for hr prompt and neg prompt using elem_id in after component 5/28/23
            "Negative prompt",
            "Sampling steps",
            "Sampling method",
            "Width",
            "Height",
            "Restore faces",
            "Tiling",
            "Hires. fix" if repo != "vlads" else "Hires fix",#NewNew Vlads #!update config needs a version check
            "Highres. fix",#old
            "Upscaler",#new
            "Upscale by",#new
            "Hires. steps",#NewOld,
            "Hires steps",#NewNew
            "Resize width to",#New
            "Resize height to",#New
            "Hires sampling method",#Newest 5/27/23
            "Seed",
            "Extra",
            "Variation seed",
            "Variation strength",
            "Resize seed from width",
            "Resize seed from height",
            "Firstpass width",#old now is upscaler
            "Firstpass height",#old now is upscale by
            "Denoising strength",
            "Batch count",
            "Batch size",
            "CFG Scale",
            "Image CFG Scale",
	    "Refiner",
	    "Checkpoint",
	    "Switch at",
	    "Enable ADetailer",
            "Script",
            "Input directory",
            "Output directory",
            "Inpaint batch mask directory (required for inpaint batch processing only)",
            "Resize mode",
            "Scale",
            "Mask blur",
            "Mask transparency",
            "Mask mode",
            "Masked content",
            "Inpaint area",
            "Only masked padding, pixels",
        ]
        
        if is_update_available:
            self.update_config()

        # components that pass through after_components
        self.all_components = []
 
        # Read saved settings
        PresetManager.all_presets = self.get_config(self.settings_file)

        # Initialize
        self.component_map = {k: None for k in self.available_components}
        self.additional_components_map = {k:None for k in self.additional_components_for_presets["additionalComponents"]}
        self.additional_components = [x for x in self.additional_components_map] # acts like available_components list for additional components

        # combine defaults and choices
        self.component_map = {**self.component_map, **self.additional_components_map}
        self.available_components = self.available_components + self.additional_components


    
    def fakeinit(self, *args, **kwargs):
        """
        __init__ workaround, since some data is not available during instantiation, such as is_img2img, filename, etc.
        This method is called from .show(), as that's the first method ScriptRunner calls after handing some state dat (is_txt2img, is_img2img2)
        """
        #self.elm_prfx = f"{'txt2img' if self.is_txt2img else 'img2img'}"
        self.elm_prfx = "preset-util"


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

        # instance level
        # quick set tab
        self.stackable_check = gr.Checkbox(value=True, label="Stackable", elem_id=f"{self.elm_prfx}_stackable_check", render=False)
        #self.save_as = gr.Text(render=False, label="Quick Save", elem_id=f"{self.elm_prfx}_save_qs_txt")
        #self.save_button = gr.Button(value="Save", variant="secondary", render=False, visible=False, elem_id=f"{self.elm_prfx}_save_qs_bttn")


        # Detailed Save
        self.stackable_check_det = gr.Checkbox(value=True, label="Stackable", elem_id=f"{self.elm_prfx}_stackable_check_det", render=False)
        self.save_detail_md = gr.Markdown(render=False, value="<center>Options are all options hardcoded, and additional you added in additional_components.py</center>\
            <center>Make your choices, adjust your settings, set a name, save. To edit a prior choice, select from dropdown and overwrite.</center>\
            <center>To apply, go to quick set. Save now works immediately in other tab without restart, filters out non-common between tabs.</center>\
            <center>Settings stack. If it's not checked, it wont overwrite. Apply one, then another. Reset is old, update how you need.</center>\
                <center>Stackable checkbox is not used for saves, it's used when making a selection from the dropdown, whether to apply as stackable or not</center>", elem_id=f"{self.elm_prfx}_mess_qs_md")
        self.save_detailed_as = gr.Text(render=False, label="Detailed Save As", elem_id=f"{self.elm_prfx}_save_ds_txt")
        self.save_detailed_button = gr.Button(value="Save", variant="primary", render=False, visible=False, elem_id=f"{self.elm_prfx}_save_ds_bttn")
        self.save_detailed_delete_button = gr.Button(value="❌Delete", render=False, elem_id=f"{self.elm_prfx}_del_ds_bttn")
        # **********************************           NOTE  ********************************************
        # NOTE: This fix uglified the code ui is now _ui, row created in before_component, stored in var, used in after_component
        # ! TODO: Keep an eye out on this, could cause confusion, if it does, either go single checkboxes with others visible False, or ...
        # Potential place to put this, in after_components elem_id txt_generation_info_button or img2img_generation_info button
        #self.save_detailed_checkbox_group = gr.CheckboxGroup(render=False, choices=list(x for x in self.available_components if self.component_map[x] is not None), elem_id=f"{self.elm_prfx}_select_ds_chckgrp")


        # Restart tab
        self.gr_restart_bttn = gr.Button(value="Restart", variant="primary", render=False, elem_id=f"{self.elm_prfx}_restart_bttn")


        # Print tab
        self.gather_button = gr.Button(value="Gather", render = False, variant="primary", elem_id=f"{self.elm_prfx}_gather_bttn")         # Helper button to print component map
        self.inspect_dd = gr.Dropdown(render = False, type="index", interactive=True, elem_id=f"{self.elm_prfx}_inspect_dd")
        self.inspect_ta = gr.TextArea(render=False, elem_id=f"{self.elm_prfx}_inspect_txt")


        self.info_markdown = gr.Markdown(value="<center>!⚠! THIS IS IN ALPHA !⚠!</center>\n\
<center>🐉 I WILL INTRODUCE SOME BREAKING CHANGES (I will try to avoid it) 🐉</center>\
<center>🙏 Please recommend your favorite script composers to implement element id's 🙏</center>\n\
<br>\
<center>If they implement unique element id's, they can get support for presets without making their own</center>\
<center>❗ I have not added element id support yet, there are more labels than id's ❗</center>\
<br>\
<center>❗❗But labels sometimes collide. I can't do 'Mask Blur' because it also matches 'Mask Blur' in scripts❗❗</center>\
<center>Try adding a component label to additional_components.json with element id 'null' without quotes for None</center>\
<br>\
<center><strong>I would like to support all custom scripts, but need script path/name/title, some distinguishing factor</strong></center>\
<center>through the kwargs in IOComponent_init 'after_compoenet' and 'before_component'</center>\
<center><link>https://github.com/Gerschel/sd_web_ui_preset_utils</link></center>", render=False)


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
            with gr.Accordion(label="Preset Manager", open = True, elem_id=f"{'txt2img' if self.is_txt2img else 'img2img'}_preset_manager_accordion"):
                with gr.Row(equal_height = True):
                    if self.is_txt2img:
                        PresetManager.txt2img_preset_dropdown.render()
                    else:
                        PresetManager.img2img_preset_dropdown.render()
                    #with gr.Column(elem_id=f"{self.elm_prfx}_ref_del_col_qs"):
                        #self.stackable_check.render()

    def after_component(self, component, **kwargs):
        if hasattr(component, "label") or hasattr(component, "elem_id"):
            self.all_components.append(self.compinfo(
                                                      component=component,
                                                      label=component.label if hasattr(component, "label") else None,
                                                      elem_id=component.elem_id if hasattr(component, "elem_id") else None,
                                                      kwargs=kwargs
                                                     )
                                      )
        label = kwargs.get("label")
        ele = kwargs.get("elem_id")
        # TODO: element id
        #if label in self.component_map or label in self.additional_components_map:# and ele == self.additional_components["additionalComponents"]) or (ele == self.additional_components["additionalComponents"]):
        if label in self.component_map:# and ele == self.additional_components["additionalComponents"]) or (ele == self.additional_components["additionalComponents"]):
            #!Hack to remove conflict between main Prompt and hr Prompt
            if self.component_map[label] is None:
                self.component_map.update({component.label: component})
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
 

    def save_detailed_fetch_valid_values_from_preset(self, stackable_flag, selection, *comps_vals):
        """
            Fetches selected preset from dropdown choice and filters valid components from choosen preset
            non-valid components will still have None as the page didn't contain any
        """
        return [[ comp_name for comp_name in PresetManager.all_presets[selection] ], gr.update(value = selection)] + self.fetch_valid_values_from_preset(stackable_flag, selection, *comps_vals)

    def delete_preset(self, selection, filepath):
        """Delete preset from local memory and write file with it removed
            filepath is not hardcoded so it can be used with other preset profiles if support gets added for loading additional presets from shares
        """
        #For writing and keeping front-end in sync with back-end
        PresetManager.all_presets.pop(selection)
        #Keep front-end in sync with backend
        PresetManager.txt2img_preset_dropdown.choice = PresetManager.all_presets.keys()
        PresetManager.img2img_preset_dropdown.choice = PresetManager.all_presets.keys()
        PresetManager.txt2img_save_detailed_name_dropdown.choice = PresetManager.all_presets.keys()
        PresetManager.img2img_save_detailed_name_dropdown.choice = PresetManager.all_presets.keys()
        file = os.path.join(PresetManager.BASEDIR, filepath)
        with open(file, 'w') as f:
            json.dump(PresetManager.all_presets, f, indent=4)
        return [gr.Dropdown.update(choices= list(PresetManager.all_presets.keys()), value=list(PresetManager.all_presets.keys())[0])] * 4

    def local_request_restart(self):
        "Restart button"
        shared.state.interrupt()
        shared.state.need_restart = True

