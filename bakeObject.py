import bpy
import os


# All objects in the folder below will have the texture baked and exported as an *.obj file
folder = "C:\\Users\\Rim\\Downloads\\uploads_files_844080_Trees+&+Bushes\\Trees & Bushes\\"
for root, directories, files in os.walk(folder):
    # Add the names of the files to the list
    for file in files:
        # Image node path
        filename, file_ext = os.path.splitext(file)
        image_node_path = folder + filename + '.png'
        exported_obj_path = folder + filename + '.obj'
        image = bpy.data.images.new("Empty", width=512, height=512)
        image.save_render(image_node_path)
        image = bpy.data.images.load(image_node_path)

        # Set the path to the FBX file
        fbx_file = folder + filename + '.fbx'

        # Import the FBX file
        bpy.ops.import_scene.fbx(filepath=fbx_file, global_scale=10)

        # Get all objects in the scene
        objects = bpy.data.objects

        # Filter the objects by type
        mesh_objects = [obj for obj in objects if obj.type == 'MESH']

        # Get the imported object
        imported_object = mesh_objects[0]
        print(f"imported object:  {imported_object}")

        # Iterate over the materials of the object
        for i, material in enumerate(imported_object.material_slots):
            # Get the base color of the material
            base_color = material.material.node_tree.nodes['Principled BSDF'].inputs['Base Color']

            # Get the node tree of the material
            node_tree = material.material.node_tree

            # Create a Diffuse BSDF node
            diffuse_node = node_tree.nodes.new(type='ShaderNodeBsdfDiffuse')

            # Set the base color of the Diffuse BSDF node
            diffuse_node.inputs['Color'].default_value = base_color.default_value

            # Print the index, name, and base color of the material
            print(
                f"Material {i}: {material.name} - Base Color: {base_color.default_value}")

            # Get the Material Output node
            output_node = node_tree.nodes['Material Output']

            # Create a link between the Diffuse BSDF node and the Material Output node
            node_tree.links.new(
                diffuse_node.outputs['BSDF'], output_node.inputs['Surface'])

            # Remove the Principled BSDF node from the node tree
            node_tree.nodes.remove(node_tree.nodes['Principled BSDF'])

            image_node = node_tree.nodes.new("ShaderNodeTexImage")

            # Set the image for the node
            image_node.image = image

            # make sure the image node is selected
            node_tree.nodes.active = image_node

            # Add the image texture node to the material
            # diffuse_node = node_tree.nodes.get("Diffuse BSDF")

        # START THE BAKING PROCESS

        # Set the render engine to Cycles
        bpy.context.scene.render.engine = 'CYCLES'

        # Set the number of samples to 10
        bpy.context.scene.cycles.samples = 10

        scene = bpy.context.scene
        for obj in scene.objects:
            obj.select_set(False)

        for obj in scene.objects:
            if obj.type != 'MESH':
                continue
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.bake(type='DIFFUSE', save_mode='EXTERNAL',
                                filepath=image_node_path)
            image.save()

        for i, material in enumerate(imported_object.material_slots):
            image_node = None
            diffuse_node = None
            material_output_node = None

            node_tree = material.material.node_tree
            for node in node_tree.nodes:
                print(node.bl_idname)
                if node.bl_idname == 'ShaderNodeTexImage':
                    # This is the image texture node
                    image_node = node
                if node.bl_idname == 'ShaderNodeBsdfDiffuse':
                    # This is the image texture node
                    diffuse_node = node
                if node.bl_idname == 'ShaderNodeOutputMaterial':
                    # This is the image texture node
                    material_output_node = node

                if node.bl_idname == 'ShaderNodeNormalMap':
                    node_tree.nodes.remove(node)

            principled_bsdf_node = node_tree.nodes.new(
                type='ShaderNodeBsdfPrincipled')
            node_tree.links.new(
                image_node.outputs['Color'], principled_bsdf_node.inputs['Base Color'])
            node_tree.links.new(
                principled_bsdf_node.outputs['BSDF'], material_output_node.inputs['Surface'])

        bpy.context.view_layer.objects.active = imported_object
        imported_object.select_set(True)

        # Export the object
        bpy.ops.export_scene.obj(
            filepath=exported_obj_path, use_selection=True)

        # Delete the object
        bpy.data.objects.remove(imported_object)
