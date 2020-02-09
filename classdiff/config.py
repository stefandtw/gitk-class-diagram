class Config:
    def load_defaults():
        pass


Config.show_nested_classes = False
Config.find_rel_scope_using_line_numbers = True
Config.cluster_packages = True
Config.hide_single_file_packages = True
Config.show_attr_type = True
Config.show_op_return_type = False
Config.show_visibility = True
Config.show_single_scope_file_border = False
Config.font = "Roboto, Verdana, Arial"
Config.font_size_classname = 18
Config.font_size_other = 11
Config.bg_removed = "#ffaaaa"
Config.bg_added = "#aaffaa"
Config.bg_changed = "#ddf3ff"
Config.bg_neutral = "#fff3d0"
Config.fg_removed = "#dd0000"
Config.fg_added = "#00dd00"
Config.package_bg = "white"
Config.graph_bg = "white"
Config.file_bg = "white"
Config.package_border = "#777777"
# Higher maxiter produces better layouts, but also takes more time.
Config.maxiter = 600
# Big graphs are slow because of splines=compound. Don't use it if graphs are
# bigger than X.
Config.splines_threshold = 5000
Config.dpi = 96
