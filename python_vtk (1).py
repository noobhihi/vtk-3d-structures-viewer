#!/usr/bin/env python

"""
"""
# import collections
import vtk
import os
import pandas as pd



def main():
    # glowne parametry
    select_tissues = [1,3,4,5,6,7,8] #max 10 ,nie 0 i 2
    show_slice = 8  #ustaw tkanke, dla ktorej wyswietlic przekroje
        
    sagittal_slice=100 #0-255
    axial_slice=100   #0-255
    coronal_slice=100  #0-255

    
    # turn on(1)/off(0) slice actors
    on_sagittal_slice=1
    on_axial_slice=1
    on_coronal_slice=1
    
    number_of_tissuses=len(select_tissues) 

    fileNameSeg = "C:/Users/Emilia/project/brain-2017-01/volumes/labels/hncma-atlas.nrrd"
    print("Plik segmentacji w main:", fileNameSeg)
    
    reader_seg = vtk.vtkNrrdReader()
    reader_seg.SetFileName(fileNameSeg)  # Sprawdź, czy zmienna jest widoczna
    reader_seg.Update()

    print("Reader zaktualizowany.")


    
    
    fileName="C:/Users/Emilia/project/brain-2017-01/volumes/imaging/A1_grayT1-1mm_resample.nrrd"
    fileNameSeg="C:/Users/Emilia/project/brain-2017-01/volumes/labels/hncma-atlas.nrrd"
    tissues_names_colors_tsv = pd.read_csv('C:/Users/Emilia/project/brain-2017-01/labelinfo/hncma-atlas-lut.tsv', sep='\t')
    tissues_names_colors_ctbl=pd.read_table('C:/Users/Emilia/project/brain-2017-01/colortables/hncma-atlas-lut.ctbl', comment='#', delim_whitespace=True)

    
    for i in range(344):
        print('indeks:nazwa tkanki ',i,' : ',tissues_names_colors_tsv['label'][i])
    colors = vtk.vtkNamedColors()

    for i in range(len(tissues_names_colors_ctbl)): #tissues_names_colors_tsv ma i+1 bo na poczatku ma element backgroud
        colors.SetColor(tissues_names_colors_tsv['label'][i+1], 
                        [tissues_names_colors_ctbl["0.1"][i]/255, 
                          tissues_names_colors_ctbl["0.2"][i]/255, 
                          tissues_names_colors_ctbl["0.3"][i]/255, 
                          tissues_names_colors_ctbl["0.4"][i]/255])
        

    

      
#CZESC ODPOWIADAJACA ZA OKNO MODELI 3D
    renderer = vtk.vtkRenderer()
    renderer_widget = vtk.vtkRenderer()

    
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)

    
    render_window.AddRenderer(renderer_widget)
    renderer.SetViewport(0.0, 0.0, 0.7, 1)
    renderer_widget.SetViewport(0.7, 0.0, 1, 1)


    
    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(render_window)
    


    reader = vtk.vtkNrrdReader()
    reader.SetFileName(fileName)
    reader.Update()

    reader_seg = vtk.vtkNrrdReader()
    reader_seg.SetFileName(fileNameSeg)
    reader_seg.Update()

    



    # An outline provides context around the data.
    #
    outlineData = vtk.vtkOutlineFilter()
    outlineData.SetInputConnection(reader.GetOutputPort())
    outlineData.Update()
    
    mapOutline = vtk.vtkPolyDataMapper()
    mapOutline.SetInputConnection(outlineData.GetOutputPort())
    
    # print(mapOutline.GetCenter())
    
    outline = vtk.vtkActor()
    outline.SetMapper(mapOutline)
    outline.GetProperty().SetColor(colors.GetColor3d("Black"))
    


    
    outlineData_seg = vtk.vtkOutlineFilter()
    outlineData_seg.SetInputConnection(reader_seg.GetOutputPort())
    outlineData_seg.Update()

    mapOutline_seg = vtk.vtkPolyDataMapper()
    mapOutline_seg.SetInputConnection(outlineData_seg.GetOutputPort())
    
    outline_seg = vtk.vtkActor()
    outline_seg.SetMapper(mapOutline_seg)
    outline_seg.GetProperty().SetColor(colors.GetColor3d("Black"))
    
    

    translate_actor_vector=[mapOutline_seg.GetCenter()[i]-mapOutline.GetCenter()[i] for i in range(3)]
    outline.SetPosition(translate_actor_vector)
    
    

# slices raw data
    sagittal, axial, coronal = raw_data_slices(reader, translate_actor_vector)
    
    
    data_size = reader.GetDataExtent()
    sagittal.SetDisplayExtent(sagittal_slice, sagittal_slice, data_size[2], data_size[3], data_size[4], data_size[5]) 
    axial.SetDisplayExtent(data_size[0], data_size[1], data_size[2], data_size[3], axial_slice, axial_slice)
    coronal.SetDisplayExtent(data_size[0], data_size[1], coronal_slice, coronal_slice, data_size[4], data_size[5])


# Tissue parameters
    available_tissues = tissue_parameters(tissues_names_colors_tsv.loc[select_tissues, ['value','label']])


    #  Time some filters
    sliders = dict()
    step_size = 1.0 / number_of_tissuses
    pos_y=0.95

    for name, tissue in available_tissues.items():
        print('Tissue: {:>9s}, value: {}'.format(name, tissue['VALUE']))
        actor_tissue,sagittal_tissue,axial_tissue,coronal_tissue = create_tissue_actor(fileNameSeg, name, tissue, colors, sagittal_slice, axial_slice, coronal_slice)
  
        
        #aktor segmentacji 3d
        renderer.AddActor(actor_tissue)
        
        
        #widgets
        slider_properties = SliderProperties()
        slider_properties.value_initial = tissue['OPACITY']
        slider_properties.title = name

        slider_properties.p1 = [0.05, pos_y]
        slider_properties.p2 = [0.25, pos_y]
        pos_y -= step_size
        cb = SliderCB(actor_tissue.GetProperty())

        slider_widget = make_slider_widget(slider_properties, colors, name)
        slider_widget.SetInteractor(iren)
        slider_widget.SetAnimationModeToAnimate()
        slider_widget.EnabledOn()
        slider_widget.SetCurrentRenderer(renderer_widget)
        slider_widget.AddObserver(vtk.vtkCommand.InteractionEvent, cb)
        sliders[name] = slider_widget
        
    
    
    renderer.SetBackground(colors.GetColor3d('LightSteelBlue'))
    renderer_widget.SetBackground(colors.GetColor3d('MidnightBlue'))


    renderer.AddActor(outline_seg)
    # dodanie aktorow przekrojow 2d
    if on_sagittal_slice:
        renderer.AddActor(sagittal)
    if on_axial_slice:   
        renderer.AddActor(axial)
    if on_coronal_slice:
        renderer.AddActor(coronal)
    




  # Initial view (looking down on the dorsal surface).
    renderer.GetActiveCamera().Roll(0)
    renderer.ResetCamera()



    # camera 3d model
    camera = renderer.GetActiveCamera()
    camera.SetViewUp(0, -1, 0)
    camera.SetFocalPoint(mapOutline_seg.GetCenter())
    camera.ComputeViewPlaneNormal()
    camera.Azimuth(60.0)
    camera.Elevation(10.0)
    camera.Dolly(-200)





    
    render_window.SetSize(640, 640)
    render_window.SetWindowName('3D model')



##########################################################################################################    

   #CZESC ODPOWIADAJACA ZA OKNO PRZEKROJOW 2D


    renderer_sagittal = vtk.vtkRenderer()
    renderer_axial = vtk.vtkRenderer()
    renderer_coronal = vtk.vtkRenderer()
    
    ren_win = vtk.vtkRenderWindow()
    ren_win.AddRenderer(renderer_sagittal)
    ren_win.AddRenderer(renderer_axial)
    ren_win.AddRenderer(renderer_coronal)
    ren_win.SetWindowName('Slices')

    renderer_sagittal.SetViewport(0.0, 0.0, 1/3, 1)
    renderer_axial.SetViewport(1/3, 0.0, 2/3, 1)
    renderer_coronal.SetViewport(2/3, 0.0, 1, 1)

    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(ren_win)

    
    grey_reader = vtk.vtkNrrdReader()
    grey_reader.SetFileName(fileName)
    grey_reader.Update()
    
    segment_reader = vtk.vtkNrrdReader()
    segment_reader.SetFileName(fileNameSeg)
    segment_reader.Update()



    grey_data_size = grey_reader.GetDataExtent()
    segment_data_size = segment_reader.GetDataExtent()
    
    sagittal_grey_data_size = [sagittal_slice, sagittal_slice] + list(grey_data_size[2:6])
    sagittal_segment_data_size = [sagittal_slice, sagittal_slice] + list(segment_data_size[2:6])
   
    axial_grey_data_size = list(grey_data_size[0:4]) + [ axial_slice, axial_slice]
    axial_segment_data_size = list(segment_data_size[0:4]) + [ axial_slice, axial_slice]
    
    coronal_grey_data_size = list(grey_data_size[0:2]) + [coronal_slice, coronal_slice] + list(grey_data_size[4:6])
    coronal_segment_data_size = list(segment_data_size[0:2]) + [coronal_slice, coronal_slice] + list(segment_data_size[4:6])
    
    
    

    #tworze aktora przekroju wybrane tkanki ze segmentacja
    tissue = available_tissues[tissues_names_colors_tsv['label'][show_slice]]
    
    
    sagittal_grey_actor, sagittal_segment_actor = slice(grey_reader, segment_reader, tissue, sagittal_grey_data_size, sagittal_segment_data_size)
    axial_grey_actor, axial_segment_actor = slice(grey_reader, segment_reader, tissue, axial_grey_data_size, axial_segment_data_size)
    coronal_grey_actor, coronal_segment_actor = slice(grey_reader, segment_reader, tissue, coronal_grey_data_size, coronal_segment_data_size)

    if on_sagittal_slice:
        renderer_sagittal.AddActor(sagittal_grey_actor)
        renderer_sagittal.AddActor(sagittal_segment_actor)
        sagittal_segment_actor.SetPosition(0, 0, -0.01)
        
    if on_axial_slice:   
        renderer_axial.AddActor(axial_grey_actor)
        renderer_axial.AddActor(axial_segment_actor)
        axial_segment_actor.SetPosition(0, 0, -0.01)
    
    if on_coronal_slice:
        renderer_coronal.AddActor(coronal_grey_actor)
        renderer_coronal.AddActor(coronal_segment_actor)
        coronal_segment_actor.SetPosition(0, 0, -0.01)
        

    renderer_sagittal.SetBackground(colors.GetColor3d('LightSteelBlue'))
    renderer_axial.SetBackground(colors.GetColor3d('LightSteelBlue'))
    renderer_coronal.SetBackground(colors.GetColor3d('LightSteelBlue'))
    
    
    
    camera_distance=6
    
    # sagital slice camera
    renderer_sagittal.ResetCamera()
    cam_sagittal = renderer_sagittal.GetActiveCamera()
    cam_sagittal.SetViewUp(0, -1, 0)
    cam_sagittal.SetPosition(0,0,camera_distance)
    cam_sagittal.SetFocalPoint(sagittal_segment_actor.GetCenter())
    cam_sagittal.ComputeViewPlaneNormal()
    cam_sagittal.Azimuth(180.0)
    cam_sagittal.Roll(-90.0)
    renderer_sagittal.ResetCameraClippingRange()

    # axial slice camera
    renderer_axial.ResetCamera()
    cam_axial = renderer_axial.GetActiveCamera()
    cam_axial.SetViewUp(0, -1, 0)
    cam_axial.SetPosition(0,0,camera_distance)
    cam_axial.SetFocalPoint(axial_segment_actor.GetCenter())
    cam_axial.ComputeViewPlaneNormal()
    cam_axial.Azimuth(180.0)
    renderer_axial.ResetCameraClippingRange()

    # coronal slice camera
    renderer_coronal.ResetCamera()
    cam_coronal = renderer_coronal.GetActiveCamera()
    cam_coronal.SetViewUp(0, -1, 0)
    cam_coronal.SetPosition(0,0,camera_distance)
    cam_coronal.SetFocalPoint(coronal_segment_actor.GetCenter())
    cam_coronal.ComputeViewPlaneNormal()
    cam_coronal.Azimuth(180.0)
    cam_coronal.Roll(-90.0)
    renderer_coronal.ResetCameraClippingRange()


    
    render_window.Render()
    ren_win.SetSize(640, 640)
    ren_win.Render()
    iren.Initialize()
    iren.Start()

# 000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000








def slice(grey_reader, segment_reader, tissue, grey_data_size, segment_data_size):
    wllut = vtk.vtkWindowLevelLookupTable()
    wllut.SetWindow(255)
    wllut.SetLevel(128)
    wllut.SetTableRange(0, 255)
    wllut.Build()


    #wybranie tkanki
    select_tissue = vtk.vtkImageThreshold()
    select_tissue.ThresholdBetween(tissue['VALUE'],tissue['VALUE'])#####################################
    select_tissue.SetInValue(255)
    select_tissue.SetOutValue(0)
    select_tissue.SetInputConnection(segment_reader.GetOutputPort())
    last_connection = select_tissue

    shrinker = vtk.vtkImageShrink3D()
    shrinker.SetInputConnection(last_connection.GetOutputPort())
    shrinker.SetShrinkFactors(tissue['SAMPLE_RATE'])
    shrinker.AveragingOn()
    last_connection = shrinker


    gaussian = vtk.vtkImageGaussianSmooth()
    gaussian.SetStandardDeviation(*tissue['GAUSSIAN_STANDARD_DEVIATION'])
    gaussian.SetRadiusFactors(*tissue['GAUSSIAN_RADIUS_FACTORS'])
    gaussian.SetInputConnection(shrinker.GetOutputPort())

    

    #surowe dane
    grey_padder = vtk.vtkImageConstantPad()
    grey_padder.SetInputConnection(grey_reader.GetOutputPort())
    grey_padder.SetOutputWholeExtent(grey_data_size)
    grey_padder.SetConstant(0)

    grey_plane = vtk.vtkPlaneSource()


    grey_mapper = vtk.vtkPolyDataMapper()
    grey_mapper.SetInputConnection(grey_plane.GetOutputPort())

    grey_texture = vtk.vtkTexture()
    grey_texture.SetInputConnection(grey_padder.GetOutputPort())
    grey_texture.SetLookupTable(wllut)
    grey_texture.SetColorModeToMapScalars()
    grey_texture.InterpolateOff()

    grey_actor = vtk.vtkActor()
    grey_actor.SetMapper(grey_mapper)
    grey_actor.SetTexture(grey_texture)


    
    
    #segmentacja
    segment_padder = vtk.vtkImageConstantPad()
    segment_padder.SetInputConnection(gaussian.GetOutputPort())
    segment_padder.SetOutputWholeExtent(segment_data_size)
    segment_padder.SetConstant(0)

    segment_plane = vtk.vtkPlaneSource()

    lut = create_head_lut(vtk.vtkNamedColors())

    segment_mapper = vtk.vtkPolyDataMapper()
    segment_mapper.SetInputConnection(segment_plane.GetOutputPort())

    segment_texture = vtk.vtkTexture()
    segment_texture.SetInputConnection(segment_padder.GetOutputPort())
    segment_texture.SetLookupTable(lut)
    segment_texture.SetColorModeToMapScalars()
    segment_texture.InterpolateOff()

    segment_actor = vtk.vtkActor()
    segment_actor.SetMapper(segment_mapper)
    segment_actor.SetTexture(segment_texture)
    segment_actor.GetProperty().SetOpacity(.5)

    
    
    return grey_actor, segment_actor







def create_head_lut(colors):
    lut = vtk.vtkLookupTable()
    lut.SetNumberOfColors(10)
    lut.SetTableRange(0, 9)
    lut.Build()
   
    lut.SetTableValue(0, colors.GetColor4d('black')) 
    lut.SetTableValue(1, colors.GetColor4d('cyan')) 
    lut.SetTableValue(2, colors.GetColor4d('cyan'))  
    lut.SetTableValue(3, colors.GetColor4d('cyan'))
    lut.SetTableValue(4, colors.GetColor4d('cyan'))  
    lut.SetTableValue(5, colors.GetColor4d('cyan')) 
    lut.SetTableValue(6, colors.GetColor4d('cyan'))  
    lut.SetTableValue(7, colors.GetColor4d('cyan'))
    lut.SetTableValue(8, colors.GetColor4d('cyan'))
    lut.SetTableValue(9, colors.GetColor4d('cyan'))

    return lut


class SliderCB:
    def __init__(self, actor_property):
        self.actorProperty = actor_property

    def __call__(self, caller, ev):
        slider_widget = caller
        value = slider_widget.GetRepresentation().GetValue()
        self.actorProperty.SetOpacity(value)

class SliderProperties:
    tube_width = 0.008
    slider_length = 0.04
    title_height = 0.015
    label_height = 0.01

    value_minimum = 0.0
    value_maximum = 1.0
    value_initial = 1.0

    p1 = [0.1, 0.1]
    p2 = [0.05, 0.1]

    title = None

    title_color = 'MistyRose'
    value_color = 'Cyan'
    slider_color = 'Coral'
    selected_color = 'Lime'
    bar_color = 'Yellow'
    bar_ends_color = 'Gold'


def make_slider_widget(properties, colors, name):
    slider = vtk.vtkSliderRepresentation2D()

    slider.SetMinimumValue(properties.value_minimum)
    slider.SetMaximumValue(properties.value_maximum)
    slider.SetValue(properties.value_initial)
    slider.SetTitleText(properties.title)

    slider.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
    slider.GetPoint1Coordinate().SetValue(properties.p1[0], properties.p1[1])
    slider.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
    slider.GetPoint2Coordinate().SetValue(properties.p2[0], properties.p2[1])

    slider.SetTubeWidth(properties.tube_width)
    slider.SetSliderLength(properties.slider_length)
    slider.SetTitleHeight(properties.title_height)
    slider.SetLabelHeight(properties.label_height)

    # Set the color properties
    # Change the color of the bar.
    slider.GetTubeProperty().SetColor(colors.GetColor3d(properties.bar_color))
    # Change the color of the ends of the bar.
    slider.GetCapProperty().SetColor(colors.GetColor3d(properties.bar_ends_color))
    # Change the color of the knob that slides.
    slider.GetSliderProperty().SetColor(colors.GetColor3d(properties.slider_color))
    # Change the color of the knob when the mouse is held on it.
    slider.GetSelectedProperty().SetColor(colors.GetColor3d(properties.selected_color))
    # Change the color of the text displaying the value.
    slider.GetLabelProperty().SetColor(colors.GetColor3d(properties.value_color))
    # Change the color of the text indicating what the slider controls
    slider.GetTitleProperty().SetColor(colors.GetColor3d(name))
    slider.GetTitleProperty().ShadowOff()


    slider_widget = vtk.vtkSliderWidget()
    slider_widget.SetRepresentation(slider)

    return slider_widget


  
def raw_data_slices(reader, translate_actor_vector):
        # Start by creating a black/white lookup table.
    bwLut = vtk.vtkLookupTable()
    bwLut.SetTableRange(0, 2000)
    bwLut.SetSaturationRange(0, 0)
    bwLut.SetHueRange(0, 0)
    bwLut.SetValueRange(0, 1)
    bwLut.Build()  # effective built

    
    sagittalColors = vtk.vtkImageMapToColors()
    sagittalColors.SetInputConnection(reader.GetOutputPort())
    sagittalColors.SetLookupTable(bwLut)
    sagittalColors.Update()

    sagittal = vtk.vtkImageActor()
    sagittal.GetMapper().SetInputConnection(sagittalColors.GetOutputPort())
    sagittal.SetPosition(translate_actor_vector)
    
    
    axialColors = vtk.vtkImageMapToColors()
    axialColors.SetInputConnection(reader.GetOutputPort())
    axialColors.SetLookupTable(bwLut)
    axialColors.Update()

    axial = vtk.vtkImageActor()
    axial.GetMapper().SetInputConnection(axialColors.GetOutputPort())
    axial.SetPosition(translate_actor_vector)
    
    
    coronalColors = vtk.vtkImageMapToColors()
    coronalColors.SetInputConnection(reader.GetOutputPort())
    coronalColors.SetLookupTable(bwLut)
    coronalColors.Update()

    coronal = vtk.vtkImageActor()
    coronal.GetMapper().SetInputConnection(coronalColors.GetOutputPort())
    coronal.SetPosition(translate_actor_vector)

    return  sagittal, axial, coronal




def create_tissue_actor(fileNameSeg, name, tissue, lut, sagittal_slice, axial_slice, coronal_slice):
    reader = vtk.vtkNrrdReader()
    reader.SetFileName(fileNameSeg)
    reader.Update()

    last_connection = reader


    select_tissue = vtk.vtkImageThreshold()
    select_tissue.ThresholdBetween(tissue['VALUE'],tissue['VALUE'])
    select_tissue.SetInValue(255)
    select_tissue.SetOutValue(0)
    select_tissue.SetInputConnection(last_connection.GetOutputPort())
    last_connection = select_tissue

    shrinker = vtk.vtkImageShrink3D()
    shrinker.SetInputConnection(last_connection.GetOutputPort())
    shrinker.SetShrinkFactors(tissue['SAMPLE_RATE'])
    shrinker.AveragingOn()
    last_connection = shrinker

    gaussian = vtk.vtkImageGaussianSmooth()
    gaussian.SetStandardDeviation(*tissue['GAUSSIAN_STANDARD_DEVIATION'])
    gaussian.SetRadiusFactors(*tissue['GAUSSIAN_RADIUS_FACTORS'])
    gaussian.SetInputConnection(shrinker.GetOutputPort())
    last_connection = gaussian
    
    iso_value = tissue['VALUE']
  
    iso_surface = vtk.vtkMarchingCubes()
    iso_surface.SetInputConnection(last_connection.GetOutputPort())
    iso_surface.ComputeScalarsOff()
    iso_surface.ComputeGradientsOff()
    iso_surface.ComputeNormalsOff()
    iso_surface.SetValue(0, iso_value)
    timer = vtk.vtkExecutionTimer()
    timer.SetFilter(iso_surface)
    iso_surface.Update()
    
    last_connection=iso_surface

    smoother = vtk.vtkWindowedSincPolyDataFilter()
    smoother.SetInputConnection(last_connection.GetOutputPort())
    smoother.SetNumberOfIterations(tissue['SMOOTH_ITERATIONS'])
    smoother.BoundarySmoothingOff()
    smoother.FeatureEdgeSmoothingOff()
    smoother.SetFeatureAngle(tissue['SMOOTH_ANGLE'])
    smoother.SetPassBand(tissue['SMOOTH_FACTOR'])
    smoother.NonManifoldSmoothingOn()
    smoother.NormalizeCoordinatesOff()
    smoother.Update()

    normals = vtk.vtkPolyDataNormals()
    normals.SetInputConnection(smoother.GetOutputPort())
    normals.SetFeatureAngle(tissue['FEATURE_ANGLE'])

    stripper = vtk.vtkStripper()
    stripper.SetInputConnection(normals.GetOutputPort())
    stripper.Update()

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(stripper.GetOutputPort())
    mapper.Update()

    # Create iso-surface
    contour = vtk.vtkContourFilter()
    contour.SetInputConnection(reader.GetOutputPort())
    contour.SetValue(0, iso_value)



    cLut = vtk.vtkLookupTable()
    cLut.SetTableRange(0, 255)
    cLut.SetNumberOfColors(1)
    cLut.SetSaturationRange(0, 1)
    cLut.SetHueRange(0, 1)
    cLut.SetValueRange(0, 1)
    cLut.Build() 
    cLut.SetTableValue(0,lut.GetColor4d(name))


    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    actor.GetProperty().SetOpacity(tissue['OPACITY'])
    actor.GetProperty().SetDiffuseColor(lut.GetColor3d(name))
    actor.GetProperty().SetSpecular(0.5)
    actor.GetProperty().SetSpecularPower(10)



    sliceColors = vtk.vtkImageMapToColors()
    sliceColors.SetInputConnection(gaussian.GetOutputPort())
    sliceColors.SetLookupTable(cLut)
    sliceColors.Update()

    data_size = reader.GetDataExtent()

    sagittal = vtk.vtkImageActor()
    sagittal.GetMapper().SetInputConnection(sliceColors.GetOutputPort())
    sagittal.SetDisplayExtent(sagittal_slice, sagittal_slice, data_size[2], data_size[3], data_size[4], data_size[5]) 

    axial = vtk.vtkImageActor()
    axial.GetMapper().SetInputConnection(sliceColors.GetOutputPort())
    axial.SetDisplayExtent(data_size[0], data_size[1], data_size[2], data_size[3], axial_slice, axial_slice)

    coronal = vtk.vtkImageActor()
    coronal.GetMapper().SetInputConnection(sliceColors.GetOutputPort())
    coronal.SetDisplayExtent(data_size[0], data_size[1], coronal_slice, coronal_slice, data_size[4], data_size[5])    

    # return actors
    return actor,sagittal,axial,coronal



def default_parameters():
    p = dict()
    p['NAME'] = ''
    p['TISSUE'] = '1'
    p['VALUE'] = 127.5
    p['FEATURE_ANGLE'] = 60
    p['SMOOTH_ANGLE'] = 60
    p['SMOOTH_ITERATIONS'] = 10
    p['SMOOTH_FACTOR'] = 0.1
    p['GAUSSIAN_STANDARD_DEVIATION'] = [2, 2, 2]
    p['GAUSSIAN_RADIUS_FACTORS'] = [2, 2, 2]
    p['SAMPLE_RATE'] = [1, 1, 1]
    p['OPACITY'] = 1.0
    return p


def parameters():
    p = default_parameters()
    p['VALUE'] = 127.5
    p['SAMPLE_RATE'] = [1, 1, 1]
    p['GAUSSIAN_STANDARD_DEVIATION'] = [2, 2, 2]
    p['SMOOTH_FACTOR'] = 0.1
    return p

def tissue_parameters(label_tsv):
    t = dict()
    for value_tissue, name_tissue in zip(label_tsv['value'],label_tsv['label']):
        if name_tissue=='background' or name_tissue=='skin':
            continue
        t[name_tissue] = parameters()
        t[name_tissue]['VALUE']=value_tissue

    return t;

    



class SliceOrder:
    """
    These transformations permute image and other geometric data to maintain proper
      orientation regardless of the acquisition order. After applying these transforms with
    vtkTransformFilter, a view up of 0,-1,0 will result in the body part
    facing the viewer.
    NOTE: some transformations have a -1 scale factor for one of the components.
          To ensure proper polygon orientation and normal direction, you must
          apply the vtkPolyDataNormals filter.

    Naming (the nomenclature is medical):
    si - superior to inferior (top to bottom)
    is - inferior to superior (bottom to top)
    ap - anterior to posterior (front to back)
    pa - posterior to anterior (back to front)
    lr - left to right
    rl - right to left
    """

    def __init__(self):
        self.si_mat = vtk.vtkMatrix4x4()
        self.si_mat.Zero()
        self.si_mat.SetElement(0, 0, 1)
        self.si_mat.SetElement(1, 2, 1)
        self.si_mat.SetElement(2, 0, 1)
        self.si_mat.SetElement(3, 3, 1)

        self.is_mat = vtk.vtkMatrix4x4()
        self.is_mat.Zero()
        self.is_mat.SetElement(0, 0, 1)
        self.is_mat.SetElement(1, 2, -1)
        self.is_mat.SetElement(2, 0, 1)
        self.is_mat.SetElement(3, 3, 1)

        self.lr_mat = vtk.vtkMatrix4x4()
        self.lr_mat.Zero()
        self.lr_mat.SetElement(0, 2, -1)
        self.lr_mat.SetElement(1, 1, -1)
        self.lr_mat.SetElement(2, 0, 1)
        self.lr_mat.SetElement(3, 3, 1)

        self.rl_mat = vtk.vtkMatrix4x4()
        self.rl_mat.Zero()
        self.rl_mat.SetElement(0, 2, 1)
        self.rl_mat.SetElement(1, 1, -1)
        self.rl_mat.SetElement(2, 0, 1)
        self.rl_mat.SetElement(3, 3, 1)

        """
        The previous transforms assume radiological views of the slices (viewed from the feet). other
        modalities such as physical sectioning may view from the head. These transforms modify the original
        with a 180° rotation about y
        """

        self.hf_mat = vtk.vtkMatrix4x4()
        self.hf_mat.Zero()
        self.hf_mat.SetElement(0, 0, -1)
        self.hf_mat.SetElement(1, 1, 1)
        self.hf_mat.SetElement(2, 2, -1)
        self.hf_mat.SetElement(3, 3, 1)

    def s_i(self):
        t = vtk.vtkTransform()
        t.SetMatrix(self.si_mat)
        return t

    def i_s(self):
        t = vtk.vtkTransform()
        t.SetMatrix(self.is_mat)
        return t

    @staticmethod
    def a_p():
        t = vtk.vtkTransform()
        return t.Scale(1, -1, 1)

    @staticmethod
    def p_a():
        t = vtk.vtkTransform()
        return t.Scale(1, -1, -1)

    def l_r(self):
        t = vtk.vtkTransform()
        t.SetMatrix(self.lr_mat)
        t.Update()
        return t

    def r_l(self):
        t = vtk.vtkTransform()
        t.SetMatrix(self.lr_mat)
        return t

    def h_f(self):
        t = vtk.vtkTransform()
        t.SetMatrix(self.hf_mat)
        return t

    def hf_si(self):
        t = vtk.vtkTransform()
        t.Concatenate(self.hf_mat)
        t.Concatenate(self.si_mat)
        return t

    def hf_is(self):
        t = vtk.vtkTransform()
        t.Concatenate(self.hf_mat)
        t.Concatenate(self.is_mat)
        return t

    def hf_ap(self):
        t = vtk.vtkTransform()
        t.Concatenate(self.hf_mat)
        t.Scale(1, -1, 1)
        return t

    def hf_pa(self):
        t = vtk.vtkTransform()
        t.Concatenate(self.hf_mat)
        t.Scale(1, -1, -1)
        return t

    def hf_lr(self):
        t = vtk.vtkTransform()
        t.Concatenate(self.hf_mat)
        t.Concatenate(self.lr_mat)
        return t

    def hf_rl(self):
        t = vtk.vtkTransform()
        t.Concatenate(self.hf_mat)
        t.Concatenate(self.rl_mat)
        return t

    def get(self, order):
        """
        Returns the vtkTransform corresponding to the slice order.

        :param order: The slice order
        :return: The vtkTransform to use
        """
        if order == 'si':
            return self.s_i()
        elif order == 'is':
            return self.i_s()
        elif order == 'ap':
            return self.a_p()
        elif order == 'pa':
            return self.p_a()
        elif order == 'lr':
            return self.l_r()
        elif order == 'rl':
            return self.r_l()
        elif order == 'hf':
            return self.h_f()
        elif order == 'hfsi':
            return self.hf_si()
        elif order == 'hfis':
            return self.hf_is()
        elif order == 'hfap':
            return self.hf_ap()
        elif order == 'hfpa':
            return self.hf_pa()
        elif order == 'hflr':
            return self.hf_lr()
        elif order == 'hfrl':
            return self.hf_rl()
        else:
            s = 'No such transform "{:s}" exists.'.format(order)
            raise Exception(s)
            
        


if __name__ == '__main__':
    main()
