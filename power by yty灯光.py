import bpy
from math import radians, cos, sin
from mathutils import Vector

bl_info = {
    "name": "YTY 照明设置",
    "blender": (2, 82, 0),
    "category": "Object",
    "author": "杨庭毅",
    "version": (1, 0, 10),
    "location": "Shift + A > Light > 添加 YTY 照明设置",
    "description": "添加多个区域光和指向对象的相机，具有可自定义的设置",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "support": "COMMUNITY"
}

class AddMovingLightsProperties(bpy.types.PropertyGroup):
    light_distance: bpy.props.FloatProperty(
        name="光源距离", 
        default=2.0, 
        min=0.1, 
        description="与对象的距离", 
        update=lambda self, context: update_lights(context)
    )
    light_height: bpy.props.FloatProperty(
        name="光源高度", 
        default=2.0, 
        min=0.1, 
        description="光源的高度", 
        update=lambda self, context: update_lights(context)
    )
    light_strength: bpy.props.FloatProperty(
        name="光源强度", 
        default=200.0, 
        min=0.0, 
        description="光源的强度", 
        update=lambda self, context: update_lights(context)
    )
    light_color: bpy.props.FloatVectorProperty(
        name="光源颜色", 
        default=(1.0, 1.0, 1.0), 
        subtype='COLOR', 
        description="光源的颜色", 
        update=lambda self, context: update_lights(context)
    )
    light_orientation: bpy.props.BoolProperty(
        name="朝向对象", 
        default=True, 
        update=lambda self, context: update_lights(context)
    )
    light_count: bpy.props.IntProperty(
        name="光源数量",
        default=3,
        min=1,
        description="要创建的光源数量",
        update=lambda self, context: update_lights(context)
    )

def update_lights(context):
    props = context.scene.add_moving_lights_props
    target_object = context.scene.get("YTY_Target_Object")

    if target_object is None:
        return

    existing_lights = [obj for obj in context.collection.objects if obj.name.startswith("YTY_Light_")]

    while len(existing_lights) < props.light_count:
        light_data = bpy.data.lights.new(name="YTY_Light", type='AREA')
        light_object = bpy.data.objects.new(name=f"YTY_Light_{len(existing_lights)+1}", object_data=light_data)
        context.collection.objects.link(light_object)
        existing_lights.append(light_object)

    while len(existing_lights) > props.light_count:
        light_to_remove = existing_lights.pop()
        bpy.data.objects.remove(light_to_remove)

    for i, light_object in enumerate(existing_lights):
        light_data = light_object.data
        light_data.energy = props.light_strength
        light_data.color = props.light_color

        angle = i * (360 / len(existing_lights))
        x = props.light_distance * cos(radians(angle))
        y = props.light_distance * sin(radians(angle))
        light_object.location = target_object.location + Vector((x, y, props.light_height))

        if props.light_orientation:
            constraint = light_object.constraints.get('TrackTo')
            if not constraint:
                constraint = light_object.constraints.new(type='TRACK_TO')
                constraint.name = 'TrackTo'
            constraint.target = target_object
            constraint.track_axis = 'TRACK_NEGATIVE_Z'
            constraint.up_axis = 'UP_Y'
        else:
            light_object.constraints.clear()

    # Update camera position and orientation
    camera_name = "YTY_Camera"
    cam_object = context.scene.objects.get(camera_name)
    if cam_object:
        cam_object.location = target_object.location + Vector((0, -props.light_distance * 2, props.light_height))
        cam_constraint = cam_object.constraints.get('TrackTo')
        if not cam_constraint:
            cam_constraint = cam_object.constraints.new(type='TRACK_TO')
            cam_constraint.name = 'TrackTo'
        cam_constraint.target = target_object
        cam_constraint.track_axis = 'TRACK_NEGATIVE_Z'
        cam_constraint.up_axis = 'UP_Y'

def create_light_collection(context):
    collection_name = "YTY_Lights"
    if collection_name not in bpy.data.collections:
        new_collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(new_collection)

    for obj in context.collection.objects:
        if obj.name.startswith("YTY_Light_"):
            bpy.data.collections[collection_name].objects.link(obj)

class UpdateLightOrientationOperator(bpy.types.Operator):
    bl_idname = "object.update_light_orientation"
    bl_label = "改变朝向对象"

    def execute(self, context):
        target_object = context.active_object
        context.scene["YTY_Target_Object"] = target_object

        # 更新所有灯光的朝向
        update_lights(context)
        return {'FINISHED'}

class AddMovingLightsOperator(bpy.types.Operator):
    bl_idname = "object.add_moving_lights"
    bl_label = "添加照明设置"

    def execute(self, context):
        update_lights_and_camera(context)
        create_light_collection(context)  # 为灯光创建集合
        return {'FINISHED'}

def update_lights_and_camera(context):
    props = context.scene.add_moving_lights_props
    target_object = context.active_object
    context.scene["YTY_Target_Object"] = target_object

    if target_object is None:
        return

    existing_lights = [obj for obj in context.collection.objects if obj.name.startswith("YTY_Light_")]

    while len(existing_lights) < props.light_count:
        light_data = bpy.data.lights.new(name="YTY_Light", type='AREA')
        light_object = bpy.data.objects.new(name=f"YTY_Light_{len(existing_lights)+1}", object_data=light_data)
        context.collection.objects.link(light_object)
        existing_lights.append(light_object)

    while len(existing_lights) > props.light_count:
        light_to_remove = existing_lights.pop()
        bpy.data.objects.remove(light_to_remove)

    update_lights(context)

class LIGHT_PT_panel(bpy.types.Panel):
    bl_label = "YTY 照明设置"
    bl_idname = "LIGHT_PT_setup"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        props = context.scene.add_moving_lights_props

        layout.prop(props, "light_count")  # 光源数量
        layout.prop(props, "light_distance")  # 光源距离
        layout.prop(props, "light_height")  # 光源高度
        layout.prop(props, "light_strength")  # 光源强度
        layout.prop(props, "light_color")  # 光源颜色
        layout.prop(props, "light_orientation")  # 朝向对象

        layout.operator(AddMovingLightsOperator.bl_idname, text="添加灯光")  # 新增按钮
        layout.operator(UpdateLightOrientationOperator.bl_idname, text="改变朝向对象")  # 改变朝向对象按钮

def menu_func(self, context):
    self.layout.operator(AddMovingLightsOperator.bl_idname, text="添加 YTY 照明设置")

def register():
    bpy.utils.register_class(AddMovingLightsProperties)
    bpy.utils.register_class(AddMovingLightsOperator)
    bpy.utils.register_class(UpdateLightOrientationOperator)  # 注册朝向更新操作
    bpy.utils.register_class(LIGHT_PT_panel)

    bpy.types.Scene.add_moving_lights_props = bpy.props.PointerProperty(type=AddMovingLightsProperties)
    bpy.types.VIEW3D_MT_light_add.append(menu_func)

def unregister():
    del bpy.types.Scene.add_moving_lights_props
    bpy.utils.unregister_class(AddMovingLightsOperator)
    bpy.utils.unregister_class(UpdateLightOrientationOperator)  # 注销朝向更新操作
    bpy.utils.unregister_class(AddMovingLightsProperties)
    bpy.utils.unregister_class(LIGHT_PT_panel)
    bpy.types.VIEW3D_MT_light_add.remove(menu_func)

if __name__ == "__main__":
    register()
