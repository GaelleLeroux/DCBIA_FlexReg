import logging
import os
from functools import partial
from vtk.util.numpy_support import vtk_to_numpy
import vtk
import time
import numpy as np
# import sip

import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin


from qt import (QGridLayout,
                QHBoxLayout,
                QVBoxLayout,
                QCheckBox,
                QLabel,
                QLineEdit,
                QStackedWidget,
                QComboBox,
                QPushButton,
                QFileDialog,
                QSpinBox,
                QWidget,
                QTimer)


import threading
# from qt.QtCore import QTimer


from Method.make_butterfly import butterflyPatch
from Method import ComputeNormals, drawPatch,vtkMeshTeeth,vtkICP,ICP,WriteSurf
#
# ButterfkyPatch
#

class ButterfkyPatch(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "ButterfkyPatch"  # TODO: make this more human readable by adding spaces
        self.parent.categories = ["Examples"]  # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#ButterfkyPatch">module documentation</a>.
"""
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""

        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerSampleData)


#
# Register sample data sets in Sample Data module
#

def registerSampleData():
    """
    Add data sets to Sample Data module.
    """
    # It is always recommended to provide sample data for users to make it easy to try the module,
    # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

    import SampleData
    iconsPath = os.path.join(os.path.dirname(__file__), 'Resources/Icons')

    # To ensure that the source code repository remains small (can be downloaded and installed quickly)
    # it is recommended to store data sets that are larger than a few MB in a Github release.

    # ButterfkyPatch1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category='ButterfkyPatch',
        sampleName='ButterfkyPatch1',
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, 'ButterfkyPatch1.png'),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames='ButterfkyPatch1.nrrd',
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums='SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95',
        # This node name will be used when the data set is loaded
        nodeNames='ButterfkyPatch1'
    )

    # ButterfkyPatch2
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category='ButterfkyPatch',
        sampleName='ButterfkyPatch2',
        thumbnailFileName=os.path.join(iconsPath, 'ButterfkyPatch2.png'),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames='ButterfkyPatch2.nrrd',
        checksums='SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97',
        # This node name will be used when the data set is loaded
        nodeNames='ButterfkyPatch2'
    )


#
# ButterfkyPatchWidget
#

class ButterfkyPatchWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._updatingGUIFromParameterNode = False
        self.reg = Reg()

    def setup(self):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath('UI/ButterfkyPatch.ui'))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = ButterfkyPatchLogic()

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)
        self.ui.spinBoxnumberscan.valueChanged.connect(self.manageNumberWidgetScan)

        # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
        # (in the selected parameter node).


        # Make sure parameter node is initialized (needed for module reload)

        
        self.initializeParameterNode()


        self.number_widget_scan = 0
        self.list_widget_scan = []
        self.manageNumberWidgetScan(2)
        self.ui.applyButton.enabled = True
        self.ui.buttonSelectOutput.connect("clicked(bool)",partial(self.openFinder,"Output"))
        self.ui.applyButton.connect("clicked(bool)",self.on_apply_button_clicked)


        customLayout = """
<layout type="horizontal">
  <item>
    <view class="vtkMRMLViewNode" singletontag="1">
      <property name="viewlabel" action="default">1</property>
    </view>
  </item>
  <item>
    <view class="vtkMRMLViewNode" singletontag="2">
      <property name="viewlabel" action="default">2</property>
    </view>
  </item>
  <item>
    <view class="vtkMRMLViewNode" singletontag="3">
      <property name="viewlabel" action="default">3</property>
    </view>
  </item>
</layout>
"""

        customLayoutId=501

        layoutManager = slicer.app.layoutManager()
        layoutManager.layoutLogic().GetLayoutNode().AddLayoutDescription(customLayoutId, customLayout)

        # Switch to the new custom layout
        layoutManager.setLayout(customLayoutId)

    def on_apply_button_clicked(self):
        output_text = self.ui.lineEditOutput.text
        suffix_text = self.ui.lineEditSuffix.text
        self.reg.run(output_text, suffix_text)

    def manageNumberWidgetScan(self,number):
        # print(f'manage number widget scan, number : {number}')
        for i in  self.list_widget_scan:
            if i.getName()=="WidgetGo":
                self.removeWidgetScan()

        while self.number_widget_scan != number :
            if number >= self.number_widget_scan :
                self.addWidgetScan(self.number_widget_scan+1)
                self.number_widget_scan += 1
            elif number <= self.number_widget_scan :
                self.removeWidgetScan()
                self.number_widget_scan -= 1

        self.reg.setT1T2(self.list_widget_scan[0],self.list_widget_scan[1])
        
        
        


    def removeWidgetScan(self):
        mainwidgetscan = self.list_widget_scan.pop(-1).getMainWidget()
        mainwidgetscan.deleteLater()
        mainwidgetscan = None

        

    def addWidgetScan(self,title:int):
        self.list_widget_scan.append(WidgetParameter(self.ui.verticalLayout_2,self.parent,title))

    def openFinder(self,nom : str,_) -> None : 
        """
         Open finder to let the user choose is files or folder
        """ 

        self.ui.lineEditOutput.setText("/home/luciacev/Documents/Gaelle/Data/Flex_Reg/output")
        self.ui.lineEditSuffix.setText("_REG")
        
        # A GARDER
        # if nom=="Matrix":
        #     surface_folder = QFileDialog.getExistingDirectory(self.parent, "Select a scan folder")
        #     self.ui.LineEditMatrix.setText(surface_folder)

        # elif nom=="Patient":
        #     surface_folder = QFileDialog.getExistingDirectory(self.parent, "Select a scan folder")
        #     self.ui.LineEditPatient.setText(surface_folder)

        # elif nom=="Output":
        #     surface_folder = QFileDialog.getExistingDirectory(self.parent, "Select a scan folder")
        #     self.ui.lineEditOutput.setText(surface_folder)




    def cleanup(self):
        """
        Called when the application closes and the module widget is destroyed.
        """
        self.removeObservers()

    def enter(self):
        """
        Called each time the user opens this module.
        """
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self):
        """
        Called each time the user opens a different module.
        """
        # Do not react to parameter node changes (GUI wlil be updated when the user enters into the module)
        self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

    def onSceneStartClose(self, caller, event):
        """
        Called just before the scene is closed.
        """
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event):
        """
        Called just after the scene is closed.
        """
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self):
        """
        Ensure parameter node exists and observed.
        """
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())

        # Select default input nodes if nothing is selected yet to save a few clicks for the user
        if not self._parameterNode.GetNodeReference("InputVolume"):
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
            if firstVolumeNode:
                self._parameterNode.SetNodeReferenceID("InputVolume", firstVolumeNode.GetID())

    def setParameterNode(self, inputParameterNode):
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if inputParameterNode:
            self.logic.setDefaultParameters(inputParameterNode)

        # Unobserve previously selected parameter node and add an observer to the newly selected.
        # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
        # those are reflected immediately in the GUI.
        if self._parameterNode is not None:
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
        self._parameterNode = inputParameterNode
        if self._parameterNode is not None:
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

        # Initial GUI update
        self.updateGUIFromParameterNode()

    def updateGUIFromParameterNode(self, caller=None, event=None):
        """
        This method is called whenever parameter node is changed.
        The module GUI is updated to show the current state of the parameter node.
        """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
        self._updatingGUIFromParameterNode = True

        # Update node selectors and sliders
        # self.ui.outputSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolume"))
        # self.ui.invertedOutputSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolumeInverse"))
        # self.ui.invertOutputCheckBox.checked = (self._parameterNode.GetParameter("Invert") == "true")

        # Update buttons states and tooltips
        # if self._parameterNode.GetNodeReference("InputVolume") and self._parameterNode.GetNodeReference("OutputVolume"):
        #     self.ui.applyButton.toolTip = "Compute output volume"
        #     self.ui.applyButton.enabled = True
        # else:
        #     self.ui.applyButton.toolTip = "Select input and output volume nodes"
        #     self.ui.applyButton.enabled = False

        # All the GUI updates are done
        self._updatingGUIFromParameterNode = False

        

    def updateParameterNodeFromGUI(self, caller=None, event=None):
        """
        This method is called when the user makes any change in the GUI.
        The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
        """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

        self._parameterNode.SetNodeReferenceID("OutputVolume", self.ui.outputSelector.currentNodeID)
        self._parameterNode.SetParameter("Invert", "true" if self.ui.invertOutputCheckBox.checked else "false")
        self._parameterNode.SetNodeReferenceID("OutputVolumeInverse", self.ui.invertedOutputSelector.currentNodeID)

        self._parameterNode.EndModify(wasModified)



#
# ButterfkyPatchLogic
#

class ButterfkyPatchLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self,lineedit=None,
                 lineedit_teeth_left_top=None,
                 lineedit_teeth_right_top=None,
                 lineedit_teeth_left_bot=None,
                 lineedit_teeth_right_bot=None,
                 lineedit_ratio_left_top=None,
                 lineedit_ratio_right_top=None,
                 lineedit_ratio_left_bot=None,
                 lineedit_ratio_right_bot=None,
                 lineedit_adjust_left_top=None,
                 lineedit_adjust_right_top=None,
                 lineedit_adjust_left_bot=None,
                 lineedit_adjust_right_bot=None,
                 curve="",
                 middle_point="",
                 type=None):
        """
        Called when the logic class is instantiated. Can be used for initializing member variables.
        """
        ScriptedLoadableModuleLogic.__init__(self)
        self.lineedit=lineedit
        self.lineedit_teeth_left_top=lineedit_teeth_left_top
        self.lineedit_teeth_right_top=lineedit_teeth_right_top
        self.lineedit_teeth_left_bot=lineedit_teeth_left_bot
        self.lineedit_teeth_right_bot=lineedit_teeth_right_bot

        self.lineedit_ratio_left_top=lineedit_ratio_left_top
        self.lineedit_ratio_right_top=lineedit_ratio_right_top
        self.lineedit_ratio_left_bot=lineedit_ratio_left_bot
        self.lineedit_ratio_right_bot=lineedit_ratio_right_bot

        self.lineedit_adjust_left_top=lineedit_adjust_left_top
        self.lineedit_adjust_right_top=lineedit_adjust_right_top
        self.lineedit_adjust_left_bot=lineedit_adjust_left_bot
        self.lineedit_adjust_right_bot=lineedit_adjust_right_bot

        self.curve=curve
        self.middle_point=middle_point

        self.type=type

    def setDefaultParameters(self, parameterNode):
        """
        Initialize parameter node with default settings.
        """
        if not parameterNode.GetParameter("Threshold"):
            parameterNode.SetParameter("Threshold", "100.0")
        if not parameterNode.GetParameter("Invert"):
            parameterNode.SetParameter("Invert", "false")

    def process(self)->None:
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        """

        parameters = {}
        
        parameters ["lineedit"] = self.lineedit

        parameters ["lineedit_teeth_left_top"] = self.lineedit_teeth_left_top
        parameters ["lineedit_teeth_right_top"] = self.lineedit_teeth_right_top
        parameters ["lineedit_teeth_left_bot"] = self.lineedit_teeth_left_bot
        parameters ["lineedit_teeth_right_bot"] = self.lineedit_teeth_right_bot

        parameters ["lineedit_ratio_left_top"] = self.lineedit_ratio_left_top
        parameters ["lineedit_ratio_right_top"] = self.lineedit_ratio_right_top
        parameters ["lineedit_ratio_left_bot"] = self.lineedit_ratio_left_bot
        parameters ["lineedit_ratio_right_bot"] = self.lineedit_ratio_right_bot

        parameters ["lineedit_adjust_left_top"] = self.lineedit_adjust_left_top
        parameters ["lineedit_adjust_right_top"] = self.lineedit_adjust_right_top
        parameters ["lineedit_adjust_left_bot"] = self.lineedit_adjust_left_bot
        parameters ["lineedit_adjust_right_bot"] = self.lineedit_adjust_right_bot

        parameters ["curve"] = self.curve
        parameters ["middle_point"] = self.middle_point

        parameters ["type"] = self.type



        flybyProcess = slicer.modules.flex_reg_cli
        self.cliNode = slicer.cli.run(flybyProcess,None, parameters)  
        return flybyProcess


#
# ButterfkyPatchTest
#

class ButterfkyPatchTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_ButterfkyPatch1()

    def test_ButterfkyPatch1(self):
        """ Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")

        # Get/create input data

        import SampleData
        registerSampleData()
        inputVolume = SampleData.downloadSample('ButterfkyPatch1')
        self.delayDisplay('Loaded test data set')

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        threshold = 100

        # Test the module logic

        logic = ButterfkyPatchLogic()

        # Test algorithm with non-inverted threshold
        logic.process(inputVolume, outputVolume, threshold, True)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], threshold)

        # Test algorithm with inverted threshold
        logic.process(inputVolume, outputVolume, threshold, False)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], inputScalarRange[1])

        self.delayDisplay('Test passed')



class Reg:
    def __init__(self,T1=None,T2=None) -> None:
        self.T1 = T1
        self.T2 = T2

    def run(self,output_folder:str,suffix:str):


        # ICP
        methode = [vtkICP()]
        option = vtkMeshTeeth(list_teeth=[1], property="Butterfly")
        icp = ICP(methode, option=option)
        output_icp = icp.run(self.T2.getSurf().GetPolyData(), self.T1.getSurf().GetPolyData())
       
        # Apply the matrix to reg with T1 center in front of camera
        tform = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformNode')
        tform.SetMatrixTransformToParent(slicer.util.vtkMatrixFromArray(output_icp["matrix"]))
        model = self.T2.getSurf()
        model.SetAndObserveTransformNodeID(tform.GetID())
        model.HardenTransform()

        # If curve move the curve
        curve = self.T2.getCurve()
        middle_point = self.T2.getMiddle()
        if curve!=None and middle_point!=None : 
            curve.SetAndObserveTransformNodeID(tform.GetID())
            curve.HardenTransform()
            middle_point.SetAndObserveTransformNodeID(tform.GetID())
            middle_point.HardenTransform()


        # Créez une nouvelle matrice pour stocker la matrice inverse
        inverse_matrix = vtk.vtkMatrix4x4()

        # Calculate invert matrix to reg with original T1
        inverse_matrix.DeepCopy(self.T1.getMatrix())  # Copie les éléments de 'matrix' dans 'inverse_matrix'
        inverse_matrix.Invert()

        # Apply invert matrix
        transform_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformNode')
        transform_node.SetMatrixTransformToParent(inverse_matrix)
        model = self.T2.getSurf()
        model.SetAndObserveTransformNodeID(transform_node.GetID())
        model.HardenTransform()

        # SAVE NEW T2
        input_T2 = self.T2.getPath()
        outpath = input_T2.replace(os.path.dirname(input_T2),output_folder)
        fname, extension_scan = os.path.splitext(input_T2)
        slicer.util.saveNode(model, outpath.split(extension_scan)[0]+suffix+extension_scan)

        # Apply matrix to center in front of camera
        transform_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformNode')
        transform_node.SetMatrixTransformToParent(self.T1.getMatrix())
        model = self.T2.getSurf()
        model.SetAndObserveTransformNodeID(transform_node.GetID())
        model.HardenTransform()

        # View scan
        self.cleanView()
        self.viewScan(self.T2.getSurf(),self.T2.getTitle())
        self.viewScan(self.T1.getSurf(),self.T1.getTitle())

    def cleanView(self):
        viewNode1 = slicer.mrmlScene.GetSingletonNode("3", "vtkMRMLViewNode")
        modelNodes = slicer.mrmlScene.GetNodesByClass("vtkMRMLModelNode")
        modelNodes.InitTraversal()
        modelsToDelete = []
        for i in range(modelNodes.GetNumberOfItems()):
            modelNode = modelNodes.GetNextItemAsObject()
            modelDisplayNode = modelNode.GetDisplayNode()

            if modelDisplayNode and modelDisplayNode.GetViewNodeIDs() and viewNode1.GetID() in modelDisplayNode.GetViewNodeIDs():
                modelsToDelete.append(modelNode)
        
        for model in modelsToDelete:
            slicer.mrmlScene.RemoveNode(model)


    def viewScan(self, surf,title: str):

        # Récupérer tous les vtkMRMLViewNodes disponibles dans la scène
        viewNodes = slicer.mrmlScene.GetNodesByClass('vtkMRMLViewNode')
        viewNodes.UnRegister(None)  # Désenregistrer pour éviter les fuites de mémoire
        
        if viewNodes.GetNumberOfItems() < 3:
            slicer.util.errorDisplay(f"Il n'y a pas suffisamment de vues 3D disponibles pour afficher le modèle.")
            return
        
        # Original Display Node
        originalDisplayNode = surf.GetDisplayNode()
        originalDisplayNode.SetViewNodeIDs([viewNodes.GetItemAsObject(title - 1).GetID()])  # Afficher dans la vue title - 1
        
        # Créer une copie du modèle original pour la vue 2
        copied_model = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLModelNode')
        copied_model.SetAndObservePolyData(surf.GetPolyData())
        copied_model.SetName("T"+str(title) + "_copy")
        
        colors = [[255/256,51/256,153/256], [102/256,102/256,255/256]]
        # Créer un nouveau Display Node pour la copie, avec une couleur verte
        colorDisplayNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLModelDisplayNode')
        colorDisplayNode.SetColor(colors[title-1])
        colorDisplayNode.Visibility2DOff()
        colorDisplayNode.Visibility3DOn()
        slicer.mrmlScene.AddNode(colorDisplayNode)
        copied_model.SetAndObserveDisplayNodeID(colorDisplayNode.GetID())
        colorDisplayNode.SetViewNodeIDs([viewNodes.GetItemAsObject(2).GetID()])  # Afficher dans la vue 2


        # # Center the model in front of the camera
        # transform_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformNode')
        # transform_node.SetMatrixTransformToParent(matrix)
        # model = copied_model
        # model.SetAndObserveTransformNodeID(transform_node.GetID())

    
    def getName(self):
        return "Reg"
    
    def setT1T2(self,T1,T2):
        self.T1 = T1
        self.T2 = T2



class WidgetParameter:
    def __init__(self,layout,parent,title) -> None:
        self.parent_layout = layout
        self.parent = parent
        self.surf = None
        self.curve = None
        self.glue = False
        self.middle_point = None
        self.matrix = None
        self.title=title
        self.camera = True
        self.main_widget = QWidget()
        layout.addWidget(self.main_widget)
        self.maint_layout = QVBoxLayout(self.main_widget)
        self.setup(self.maint_layout,title)
        self.timer = QTimer()
        self.start_time = None

    def setup(self,layout,title):

        self.layout_file = QHBoxLayout()
        layout.addLayout(self.layout_file)
        self.label_1 = QLabel(f'Scan T{title}')
        self.lineedit = QLineEdit()
        self.button_select_scan = QPushButton('Select')
        self.button_select_scan.pressed.connect(self.selectFile)
        

        self.layout_file.addWidget(self.label_1)
        self.layout_file.addWidget(self.lineedit)
        self.layout_file.addWidget(self.button_select_scan)

        widgetView = QWidget()
        self.layoutView = QGridLayout(widgetView)
        self.button_view = QPushButton('View')
        self.button_view.pressed.connect(self.viewScan)
        self.layoutView.addWidget(self.button_view)
        layout.addWidget(widgetView)

        self.combobox_choice_method = QComboBox()
        self.combobox_choice_method.addItems(['Parameter','Landmark'])
        self.combobox_choice_method.activated.connect(self.changeMode)
        layout.addWidget(self.combobox_choice_method)



        self.stackedWidget = QStackedWidget()
        layout.addWidget(self.stackedWidget)

        #widget paramater
        widget_full_paramater = QWidget()
        self.stackedWidget.insertWidget(0,widget_full_paramater)
        self.layout_widget = QGridLayout(widget_full_paramater)

        self.layout_left_top = QGridLayout()
        self.layout_right_top = QGridLayout()
        self.layout_left_bot = QGridLayout()
        self. layout_right_bot = QGridLayout()

        self.layout_widget.addLayout(self.layout_left_top,0,0)
        self.layout_widget.addLayout(self.layout_right_top,0,1)
        self.layout_widget.addLayout(self.layout_left_bot,1,0)
        self.layout_widget.addLayout(self.layout_right_bot,1,1)


        (self.lineedit_teeth_left_top , 
         self.lineedit_ratio_left_top ,
            self.lineedit_adjust_left_top) = self.displayParamater(self.layout_left_top,1,[5,0.3,0])
        
        (self.lineedit_teeth_right_top , 
         self.lineedit_ratio_right_top ,
            self.lineedit_adjust_right_top) = self.displayParamater(self.layout_right_top,2,[12,0.3,0])
        
        (self.lineedit_teeth_left_bot , 
         self.lineedit_ratio_left_bot ,
            self.lineedit_adjust_left_bot) = self.displayParamater(self.layout_left_bot,3,[3,0.33,0])

        (self.lineedit_teeth_right_bot , 
         self.lineedit_ratio_right_bot ,
            self.lineedit_adjust_right_bot) = self.displayParamater(self.layout_right_bot,4,[14,0.33,0])
        
       
        self.button_update = QPushButton('Update')
        self.button_update.pressed.connect(self.processPatch)
        self.layout_widget.addWidget(self.button_update,2,0,1,2)

       


        

        #widget outline
        widget_outline = QWidget()
        self.stackedWidget.insertWidget(1,widget_outline)

        self.layout_outline = QGridLayout(widget_outline)
        self.button_loadmarkups = QPushButton('Load Landmarks')
        self.button_loadmarkups.pressed.connect(self.loadLandamrk)
        self.layout_outline.addWidget(self.button_loadmarkups,0,0,1,2)

        self.button_curvepoint = QPushButton('Point Curve')
        self.button_curvepoint.pressed.connect(self.curvePoint)
        self.layout_outline.addWidget(self.button_curvepoint,1,0,1,2)  

        self.add_points = QPushButton('Resample points')
        self.add_points.pressed.connect(self.addPoints)
        self.layout_outline.addWidget(self.add_points,2,0) 

        self.spin_add_points = QSpinBox()
        self.spin_add_points.setMinimum(4)
        self.spin_add_points.setValue(4)
        self.layout_outline.addWidget(self.spin_add_points,2,1) 

        self.button_placepoint = QPushButton('Middle point')
        self.button_placepoint.pressed.connect(self.placeMiddlePoint)
        self.layout_outline.addWidget(self.button_placepoint,3,0,1,2)

        self.button_draw = QPushButton('Draw')
        self.button_draw.pressed.connect(self.draw)
        self.layout_outline.addWidget(self.button_draw,4,0,1,2)

        self.layout_button_display = QGridLayout()
        layout.addLayout(self.layout_button_display)

        # self.button_view = QPushButton('View')
        # self.button_view.pressed.connect(self.viewScan)
        # self.layout_button_display.addWidget(self.button_view)

        # self.button_update = QPushButton('Update')
        # self.button_update.pressed.connect(self.processPatch)
        # self.layout_button_display.addWidget(self.button_update)

        self.label_time = QLabel(f'time')
        self.layout_button_display.addWidget(self.label_time)
        self.label_time.setVisible(False)


    def getMainWidget(self):
        return self.main_widget
    
    def getName(self):
        return "WidgetParameter"
    
    def getSurf(self):
        return self.surf
    
    def changeMode(self,index):
        self.stackedWidget.setCurrentIndex(index)

    def getPath(self):
        return self.lineedit.text
    
    def getTitle(self):
        return self.title
    
    def getCurve(self):
        return self.curve
    
    def getMiddle(self):
        return self.middle_point
    
    def getMatrix(self):
        return self.matrix



    def displayParamater(self,layout,number,parameter):
        label_teeth= QLabel(f'Teeth {number}')
        lineedit_teeth= QLineEdit(str(parameter[0]))
        label_ratio= QLabel('Ratio')
        lineedit_ratio= QLineEdit(str(parameter[1]))
        label_adjust = QLabel('Adjust')
        lineedit_adjust = QLineEdit(str(parameter[2]))

        layout.addWidget(label_teeth,0,0)
        layout.addWidget(lineedit_teeth,0,1)
        layout.addWidget(label_ratio,1,0)
        layout.addWidget(lineedit_ratio,1,1)
        layout.addWidget(label_adjust,2,0)
        layout.addWidget(lineedit_adjust,2,1)

        return lineedit_teeth, lineedit_ratio, lineedit_adjust


    def selectFile(self):
        # path_file = QFileDialog.getOpenFileName(self.parent,
        #                                         'Open a file',
        #                                         '/home',
        #                                         'VTK File (*.vtk) ;; STL File (*.stl)')
        # self.lineedit.insert(path_file)
        # if int(self.title)
        if self.title==1:
            self.lineedit.insert('/home/luciacev/Documents/Gaelle/Data/Flex_Reg/P16_T1.vtk')
        else : 
            self.lineedit.insert('/home/luciacev/Documents/Gaelle/Data/Flex_Reg/P16_T2.vtk')


    def viewScan(self):
        if self.surf == None :
            # Load model
            self.surf = slicer.util.loadModel(self.lineedit.text)

            # Get data model
            displayNode = self.surf.GetDisplayNode()
            
            # Récupérer tous les vtkMRMLViewNodes disponibles dans la scène
            viewNodes = slicer.mrmlScene.GetNodesByClass('vtkMRMLViewNode')
            viewNodes.UnRegister(None) # Désenregistrer pour éviter les fuites de mémoire
            
            customLayoutId=501
            layoutManager = slicer.app.layoutManager()
            layoutManager.setLayout(customLayoutId)

            viewNode = viewNodes.GetItemAsObject(self.title - 1) if viewNodes.GetNumberOfItems() >= self.title else None
            
            if viewNode:
                # Display model in windows
                displayNode.SetViewNodeIDs([viewNode.GetID()])

            else:
                slicer.util.errorDisplay(f"There is 3D windows available with the index : {self.title - 1}.")

            # Get data of model
            points = self.surf.GetPolyData().GetPoints()

            # Get center of model
            center = [0.0, 0.0, 0.0]
            for i in range(points.GetNumberOfPoints()):
                x, y, z = points.GetPoint(i)
                center[0] += x
                center[1] += y
                center[2] += z

            center[0] /= points.GetNumberOfPoints()
            center[1] /= points.GetNumberOfPoints()
            center[2] /= points.GetNumberOfPoints()


            # Get the focal point of the camera
            render_view = slicer.app.layoutManager().threeDWidget(0).threeDView()
            camera = render_view.renderWindow().GetRenderers().GetFirstRenderer().GetActiveCamera()
            focal_point = camera.GetFocalPoint() 
            center[0]-=focal_point[0]
            center[1]-=focal_point[1]
            center[2]-=focal_point[2]


            # Create matrix to center the vtk
            matrix = vtk.vtkMatrix4x4()
            matrix.Identity()  
            matrix.SetElement(0, 3, -center[0])  
            matrix.SetElement(1, 3, -center[1])  
            matrix.SetElement(2, 3, -center[2])  

            self.matrix = matrix

            transform_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformNode')
            transform_node.SetMatrixTransformToParent(matrix)
            model = self.surf
            #for test
            # self.camera=False
            # matrix = vtk.vtkMatrix4x4()
            # matrix.Identity()  
            # self.matrix=matrix
            #
            if self.camera :
                model.SetAndObserveTransformNodeID(transform_node.GetID())
                model.HardenTransform()

            if self.glue :
                self.curve.SetAndObserveSurfaceConstraintNode(self.surf)

        else :
            viewNode1 = slicer.mrmlScene.GetSingletonNode(str(self.title), "vtkMRMLViewNode")
            modelNodes = slicer.mrmlScene.GetNodesByClass("vtkMRMLModelNode")
            modelNodes.InitTraversal()
            modelsToDelete = []
            for i in range(modelNodes.GetNumberOfItems()):
                modelNode = modelNodes.GetNextItemAsObject()
                modelDisplayNode = modelNode.GetDisplayNode()
    
                if modelDisplayNode and modelDisplayNode.GetViewNodeIDs() and viewNode1.GetID() in modelDisplayNode.GetViewNodeIDs():
                    modelsToDelete.append(modelNode)
          
            for model in modelsToDelete:
                slicer.mrmlScene.RemoveNode(model)
            
            self.surf = None
            self.viewScan()

            




    def processPatch(self):
        modelNode = self.surf.GetPolyData()
        print("avant cli")
        self.logic = ButterfkyPatchLogic(str(self.lineedit.text),
                        int(self.lineedit_teeth_left_top.text),
                       int(self.lineedit_teeth_right_top.text),
                       int(self.lineedit_teeth_left_bot.text),
                       int(self.lineedit_teeth_right_bot.text),
                       float(self.lineedit_ratio_left_top.text),
                       float(self.lineedit_ratio_right_top.text),
                       float(self.lineedit_ratio_left_bot.text),
                       float(self.lineedit_ratio_right_bot.text),
                       float(self.lineedit_adjust_left_top.text),
                       float(self.lineedit_adjust_right_top.text),
                       float(self.lineedit_adjust_left_bot.text),
                       float(self.lineedit_adjust_right_bot.text),
                       "None",
                       "None",
                       "butterfly")
        self.logic.process()
        self.start_time = time.time()
        self.timer.timeout.connect(self.onProcessUpdateButterfly)
        self.timer.start(500)


    def onProcessUpdateButterfly(self):
        elapsed_time = time.time() - self.start_time
        self.label_time.setVisible(True)
        self.label_time.setText(f"time : {round(float(elapsed_time),2)}s")

        if elapsed_time >= 30:
            self.timer.stop()

        elif self.logic.cliNode.GetStatus() & self.logic.cliNode.Completed:
            self.viewScan()
            modelNode = self.surf.GetPolyData()
            self.displaySegmentation(self.surf)
            self.timer.stop()

    def loadLandamrk(self):
        # node = slicer.util.loadMarkups('/home/luciacev/Desktop/Data/ButterflyPatch/F.mrk.json')
        # node.SetCurveTypeToSpline()
        bounding_box = [0, 0, 0, 0, 0, 0]
        self.surf.GetRASBounds(bounding_box)
        center = [(bounding_box[1] + bounding_box[0]) / 2, (bounding_box[3] + bounding_box[2]) / 2, (bounding_box[5] + bounding_box[4]) / 2]

        self.curve = slicer.app.mrmlScene().AddNewNodeByClass("vtkMRMLMarkupsClosedCurveNode", f'T{self.title} curve')

        self.curve.AddControlPoint([center[0]+10,center[1]-10,center[2]-5],f'F1')
        self.curve.AddControlPoint([center[0]+10,center[1]+10,center[2]-5],f'F2')
        self.curve.AddControlPoint([center[0]-10,center[1]+10,center[2]-5],f'F3')
        self.curve.AddControlPoint([center[0]-10,center[1]-10,center[2]-5],f'F4')
        # self.curve.AddControlPoint([0,10,0],'F1')
        # self.curve.AddControlPoint([0,-10,0],'F2')
        # self.curve.AddControlPoint([0,10,10],'F3')
        # self.curve.AddControlPoint([0,10,-10],'F4')
        self.viewLandmark()
        


        # curve.SetAndObserveSurfaceConstrainNode(self.surf)

    def viewLandmark(self):
        viewNodes = slicer.mrmlScene.GetNodesByClass('vtkMRMLViewNode')
        viewNodes.UnRegister(None)  # Désenregistrer pour éviter les fuites de mémoire

        displayNode = self.curve.GetDisplayNode()
        if displayNode is not None:
            displayNode.SetVisibility2D(False)
            displayNode.SetVisibility3D(True)

            view_ids_to_display = [viewNodes.GetItemAsObject(self.title-1).GetID()]
            displayNode.SetViewNodeIDs(view_ids_to_display)


    def curvePoint(self):


        # surf = self.surf.GetPolyData()
        # surf_normal = ComputeNormals(surf)
        # points = surf.GetPoints()
        # normal_point = surf_normal.GetPointData().GetArray('Normal')
        # point_curve = self.curve.GetCurvePointsWorld() #return point on curve
        # out_point = vtk.vtkPoints()
        # out = self.curve.ConstrainPointsToSurface(points,normal_point,surf,out_point)
        self.curve.SetAndObserveSurfaceConstraintNode(self.surf)
        self.glue=True
        # print(f'out point {out_point}')
        # print(f'out function {out}')

        # markups_node = slicer.app.mrmlScene().AddNewNodeByClass('vtkMRMLMarkupsFiducialNode')
        # for i , point in enumerate(vtk_to_numpy(self.curve.GetCurvePointsWorld().GetData())) :
        #     markups_node.AddControlPoint(point,f'F{i}')

        

    def addPoints(self):
        # Obtenez votre noeud de courbe
        curveNode = self.curve
        curvePolyData = curveNode.GetCurveWorld()
        points = curvePolyData.GetPoints()

        # Créez des splines pour interpoler les points de la courbe
        splineX = vtk.vtkCardinalSpline()
        splineY = vtk.vtkCardinalSpline()
        splineZ = vtk.vtkCardinalSpline()

        # Ajoutez les points de la courbe aux splines
        for i in range(points.GetNumberOfPoints()):
            p = points.GetPoint(i)
            splineX.AddPoint(i, p[0])
            splineY.AddPoint(i, p[1])
            splineZ.AddPoint(i, p[2])

        # Déterminez le nombre de points souhaité
        numberOfPoints = self.spin_add_points.value
        newCurveNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsClosedCurveNode',f'T{self.title} curve')

        # Évaluez les splines à intervalles réguliers pour obtenir le nouveau set de points
        for i in range(numberOfPoints):
            u = i / (numberOfPoints - 1.0) * (points.GetNumberOfPoints() - 1)
            if i == numberOfPoints-1:
                u = u -(points.GetNumberOfPoints() - 1)/(numberOfPoints*2)
            x = splineX.Evaluate(u)
            y = splineY.Evaluate(u)
            z = splineZ.Evaluate(u)
            newCurveNode.AddControlPoint(vtk.vtkVector3d(x, y, z))

        # Si vous voulez, vous pouvez maintenant supprimer l'ancien noeud de courbe
        self.curve = newCurveNode
        slicer.mrmlScene.RemoveNode(curveNode)
        self.viewLandmark()
        if self.glue:
            self.curve.SetAndObserveSurfaceConstraintNode(self.surf)


    def placeMiddlePoint(self):
        # self.middle_point = slicer.app.mrmlScene().AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
        # self.middle_point.AddControlPoint([0,0,0],'F1')

        bounding_box = [0, 0, 0, 0, 0, 0]
        self.surf.GetRASBounds(bounding_box)
        center = [(bounding_box[1] + bounding_box[0]) / 2, (bounding_box[3] + bounding_box[2]) / 2, (bounding_box[5] + bounding_box[4]) / 2]

        self.middle_point = slicer.app.mrmlScene().AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")

        self.middle_point.AddControlPoint(center,'F1')

        viewNodes = slicer.mrmlScene.GetNodesByClass('vtkMRMLViewNode')
        viewNodes.UnRegister(None)  # Désenregistrer pour éviter les fuites de mémoire

        displayNode = self.middle_point.GetDisplayNode()
        if displayNode is not None:
            displayNode.SetVisibility2D(False)
            displayNode.SetVisibility3D(True)
            view_ids_to_display = [viewNodes.GetItemAsObject(self.title-1).GetID()]
            displayNode.SetViewNodeIDs(view_ids_to_display)


    def draw(self):
        
        # Move the curve and the middle point where the original model is located
        inverse_matrix = vtk.vtkMatrix4x4()

        # Calculate invert matrix to reg with original T1
        inverse_matrix.DeepCopy(self.getMatrix()) 
        inverse_matrix.Invert()

        transform_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformNode')
        transform_node.SetMatrixTransformToParent(inverse_matrix)

        self.curve.SetAndObserveTransformNodeID(transform_node.GetID())
        self.curve.HardenTransform()
        self.middle_point.SetAndObserveTransformNodeID(transform_node.GetID())
        self.middle_point.HardenTransform()

        self.camera=False
        self.viewScan()
        self.curve.SetAndObserveSurfaceConstraintNode(self.surf)

        middle_point_vector3D = self.middle_point.GetNthControlPointPositionWorld(0)
        
        # put the data in str type
        vector_middle = ','.join([str(middle_point_vector3D.GetX()), str(middle_point_vector3D.GetY()), str(middle_point_vector3D.GetZ())])
        list_curve = list(vtk_to_numpy(self.curve.GetCurvePointsWorld().GetData()))
        list_curve_str = ','.join(map(str, list_curve))   
        vector_middle="["+vector_middle+"]"

        # CLI 
        self.logic = ButterfkyPatchLogic(str(self.lineedit.text),
                        int(self.lineedit_teeth_left_top.text),
                       int(self.lineedit_teeth_right_top.text),
                       int(self.lineedit_teeth_left_bot.text),
                       int(self.lineedit_teeth_right_bot.text),
                       float(self.lineedit_ratio_left_top.text),
                       float(self.lineedit_ratio_right_top.text),
                       float(self.lineedit_ratio_left_bot.text),
                       float(self.lineedit_ratio_right_bot.text),
                       float(self.lineedit_adjust_left_top.text),
                       float(self.lineedit_adjust_right_top.text),
                       float(self.lineedit_adjust_left_bot.text),
                       float(self.lineedit_adjust_right_bot.text),
                       list_curve_str,
                       vector_middle,
                       "curve")
        self.logic.process()

        self.start_time = time.time()
        self.timer.timeout.connect(self.onProcessUpdateCurve)
        self.timer.start(500)


        


    def onProcessUpdateCurve(self):
        elapsed_time = time.time() - self.start_time
        self.label_time.setVisible(True)
        self.label_time.setText(f"time : {round(float(elapsed_time),2)}s")

        if elapsed_time >= 30:
            self.timer.stop()

        elif self.logic.cliNode.GetStatus() & self.logic.cliNode.Completed:
            #PLACE BACK THE CURVE AND THE MIDDLE POINT ON THE CENTER MODEL 
            transform_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTransformNode')
            transform_node.SetMatrixTransformToParent(self.matrix)

            self.curve.SetAndObserveTransformNodeID(transform_node.GetID())
            self.curve.HardenTransform()
            self.middle_point.SetAndObserveTransformNodeID(transform_node.GetID())
            self.middle_point.HardenTransform()

            # Load the new model and display the patch 
            self.camera=True
            self.viewScan()
            self.curve.SetAndObserveSurfaceConstraintNode(self.surf)
            self.displaySegmentation(self.surf)
            self.timer.stop()




    def displaySurf(self,surf):
        mesh = slicer.app.mrmlScene().AddNewNodeByClass("vtkMRMLModelNode", 'First data')
        mesh.SetAndObservePolyData(surf)
        mesh.CreateDefaultDisplayNodes()




    def displaySegmentation(self,model_node):
        displayNode = model_node.GetModelDisplayNode()
        displayNode.SetScalarVisibility(False)
        disabledModify = displayNode.StartModify()
        displayNode.SetActiveScalarName("Butterfly")
        displayNode.SetScalarVisibility(True)
        displayNode.EndModify(disabledModify)