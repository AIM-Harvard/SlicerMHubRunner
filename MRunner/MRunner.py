import logging
import os, json

import vtk

import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import qt


#
# MRunner
#

class MRunner(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "MRunner"  # TODO: make this more human readable by adding spaces
        self.parent.categories = ["Examples"]  # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#MRunner">module documentation</a>.
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

    # MRunner1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category='MRunner',
        sampleName='MRunner1',
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, 'MRunner1.png'),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames='MRunner1.nrrd',
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums='SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95',
        # This node name will be used when the data set is loaded
        nodeNames='MRunner1'
    )

    # MRunner2
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category='MRunner',
        sampleName='MRunner2',
        thumbnailFileName=os.path.join(iconsPath, 'MRunner2.png'),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames='MRunner2.nrrd',
        checksums='SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97',
        # This node name will be used when the data set is loaded
        nodeNames='MRunner2'
    )


#
# MRunnerWidget
#

class MRunnerWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
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

    def setup(self):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        logging.info('>>>>>>>> MRunnerWidget Setup')
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath('UI/MRunner.ui'))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = MRunnerLogic()
        self.logic.logCallback = self.addLog
        self.logic.resourcePath = self.resourcePath

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
        # (in the selected parameter node).
        self.ui.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
        self.ui.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
        self.ui.outputSegmentationSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
        #self.ui.outputSegmentationSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.ui.segmentationShow3DButton.setSegmentationNode)
        self.ui.imageThresholdSliderWidget.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
        self.ui.downloadDockerfileCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)
        self.ui.gpuCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)
        self.ui.dockerNoCacheCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)
        #self.ui.invertedOutputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
        self.ui.modelComboBox.currentTextChanged.connect(self.updateParameterNodeFromGUI)

        # install required python packages and add file-path to pythonpath (NOTE: the latter seems only required on linux?)
        self.logic.setupPythonRequirements()
        import sys
        sys.path.insert(0, os.path.join(os.getcwd(), 'MRunner'))

        # load repo definition and pass down to logic
        from Utils.Repo import Repository
        self.repo = Repository(self.resourcePath('Dockerfiles/repo.json'))
        self.logic.repo = self.repo

        # exract model names from repo definition and feed into dropdown
        for model in self.repo.getModels():
            self.ui.modelComboBox.addItem(f"{model.getName()} ({model.getDockerfile().REPOSITORY}:{model.getDockerfile().getImageName()})", model)

        # test table view
        self.ui.modelTableWidget.setRowCount(2)
        self.ui.modelTableWidget.setColumnCount(2)
        self.ui.modelTableWidget.setColumnWidth(100, 200)
        self.ui.modelTableWidget.setItem(0,0, qt.QTableWidgetItem("Name"))
        self.ui.modelTableWidget.setItem(0,1, qt.QTableWidgetItem("Name"))
        self.ui.modelTableWidget.setVisible(False)

        # test list view
        self.ui.modelListWidget.addItem("test")
        self.ui.modelListWidget.setVisible(False)

        # Buttons
        self.ui.applyButton.connect('clicked(bool)', self.onApplyButton)
        self.ui.advancedCollapsibleButton.collapsed = False
        self.ui.cmdTest1.connect('clicked(bool)', self.onTest1ButtonClick)
        self.ui.cmdTest2.connect('clicked(bool)', self.onTest2ButtonClick)

        # disable old components (TODO: remove them later)
        self.ui.imageThresholdSliderWidget.setVisible(False)
        self.ui.outputSelector.setVisible(False)
        self.ui.label_2.setVisible(False)
        self.ui.label_3.setVisible(False)
        self.ui.cmdTest1.setVisible(False)
        self.ui.cmdTest2.setVisible(False)

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

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
        self.ui.inputSelector.setCurrentNode(self._parameterNode.GetNodeReference("InputVolume"))
        self.ui.outputSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolume"))
        self.ui.outputSegmentationSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputSegmentation"))
        #self.ui.invertedOutputSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolumeInverse"))
        self.ui.imageThresholdSliderWidget.value = float(self._parameterNode.GetParameter("Threshold"))
        self.ui.dockerNoCacheCheckBox.checked = (self._parameterNode.GetParameter("DockerNoCache") == "true")

        # check if docker is installed
        isDockerInstalled = self.logic.checkForDocker()

        # model selection
        model = self.ui.modelComboBox.currentData

        # check options (how to get the docker image, either downloading the file from repo or pulling from dockerhub)
        self.updateDownloadDockerfileCheckBox(model)

        # check if the model supports gpu (effects wheather use gpu flag can be set for this model)
        self.updateGpuCheckBox(model)

        # Update buttons states and tooltips
        # TODO: Image must be either downloadable or pullable.
        #       This won't be enforced for now, as we keep the option 
        #       to build the image outside of the plugins lifecycle during development. 
        inputVolume = self._parameterNode.GetNodeReference("InputVolume")
        if inputVolume and isDockerInstalled:
            self.ui.applyButton.toolTip = "Start segmentation"
            self.ui.applyButton.enabled = True
        else:
            self.ui.applyButton.toolTip = "Select input volume nodes"
            self.ui.applyButton.enabled = False

        # output name 
        if inputVolume:
            self.ui.outputSegmentationSelector.baseName = f"{inputVolume.GetName()} [{model.getName()}]"

        # All the GUI updates are done
        self._updatingGUIFromParameterNode = False


    def updateDownloadDockerfileCheckBox(self, model):
        modelCanDownload = model.getDockerfile().isDownloadableFromRepository()
        modelCanPull = model.getDockerfile().isPullableFromRepository()
        
        if not modelCanDownload:
            # model can not be downloaded -> remove the option of downloading a model
            self.ui.downloadDockerfileCheckBox.checked = False
            self.ui.downloadDockerfileCheckBox.enabled = False
        elif not modelCanPull:
            # model can be downloaded but not pulled -> enforce download 
            self.ui.downloadDockerfileCheckBox.checked = True
            self.ui.downloadDockerfileCheckBox.enabled = False
        else:
            # leave choice free to the user
            # NOTE: case no download and no pull not catched (see self.updateGUIFromParameterNode())
            # --> in case downlaod is disabled and pulling is not possible, the image must be provided or the plugin will fail.
            self.ui.downloadDockerfileCheckBox.checked = (self._parameterNode.GetParameter("DownloadDockerfile") == "true")
            self.ui.downloadDockerfileCheckBox.enabled = True


    def updateGpuCheckBox(self, model):
        modelCanUseGPU = model.getDockerfile().isGpuUsable()

        if not modelCanUseGPU:
            self.ui.gpuCheckBox.checked = False
            self.ui.gpuCheckBox.enabled = False
        else:
            self.ui.gpuCheckBox.checked = (self._parameterNode.GetParameter("UseGPU") == "true")
            self.ui.gpuCheckBox.enabled = True


    def updateParameterNodeFromGUI(self, caller=None, event=None):
        """
        This method is called when the user makes any change in the GUI.
        The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
        """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

        self._parameterNode.SetNodeReferenceID("InputVolume", self.ui.inputSelector.currentNodeID)
        self._parameterNode.SetNodeReferenceID("OutputVolume", self.ui.outputSelector.currentNodeID)
        self._parameterNode.SetParameter("Threshold", str(self.ui.imageThresholdSliderWidget.value))
        self._parameterNode.SetParameter("DownloadDockerfile", "true" if self.ui.downloadDockerfileCheckBox.checked else "false")
        self._parameterNode.SetParameter("UseGPU", "true" if self.ui.gpuCheckBox.checked else "false")
        self._parameterNode.SetParameter("DockerNoCache", "true" if self.ui.dockerNoCacheCheckBox.checked else "false")

        # model selection
        model = self.ui.modelComboBox.currentData

        # check options (how to get the docker image, either downloading the file from repo or pulling from dockerhub)
        self.updateDownloadDockerfileCheckBox(model)

        # check if the model supports gpu (effects wheather use gpu flag can be set for this model)
        self.updateGpuCheckBox(model)

        # batch modification done
        self._parameterNode.EndModify(wasModified)

    def addLog(self, text):
        """Append text to log window
        """
        self.ui.statusLabel.appendPlainText(text)
        slicer.app.processEvents()  # force update

    def onApplyButton(self):
        """
        Run processing when user clicks "Apply" button.
        """
        with slicer.util.tryWithErrorDisplay("Failed to compute results.", waitCursor=True):

            # clear text field
            self.ui.statusLabel.plainText = ''

            # setup python requirements 
            # self.logic.setupPythonRequirements() NOTE: moved to setup()

            # Create new segmentation node, if not selected yet
            if not self.ui.outputSegmentationSelector.currentNode():
                self.ui.outputSegmentationSelector.addNode()
                self._parameterNode.SetNodeReferenceID("OutputSegmentation", self.ui.outputSegmentationSelector.currentNodeID)

            # get image tag from dropdown
            selectedModel = self.ui.modelComboBox.currentData

            # Compute output
            self.logic.process(
                model               = selectedModel,
                inputVolume         = self.ui.inputSelector.currentNode(), 
                outputSegmentation  = self.ui.outputSegmentationSelector.currentNode(),
                imageThreshold      = self.ui.imageThresholdSliderWidget.value, 
                downloadDockerfile  = self.ui.downloadDockerfileCheckBox.checked,
                useGPU              = self.ui.gpuCheckBox.checked,
                noCache             = self.ui.dockerNoCacheCheckBox.checked
            )


    def onTest1ButtonClick(self):
        self.addLog("-- Test 1 (Segmentation names) ------------")
        print("combo data: ", self.ui.modelComboBox.currentData)


    def onTest2ButtonClick(self):
        self.addLog("-- Test 2 (fake segment import from local sample data) ------------")

        ## sample data
        #sample_dir = self.resourcePath("SampleData")
        #assert os.path.isdir(sample_dir), f"Path not found: {sample_dir}"
        #self.addLog(f"Sample dir: {sample_dir}")#

        ## Create new segmentation node, if not selected yet
        #if not self.ui.outputSegmentationSelector.currentNode():
        #    self.ui.outputSegmentationSelector.addNode()
        #    self._parameterNode.SetNodeReferenceID("OutputSegmentation", self.ui.outputSegmentationSelector.currentNodeID)#

        #self.logic.displaySegmentationsFromYamlFile(
        #    self.ui.outputSegmentationSelector.currentNode(),
        #    sample_dir
        #)

#
# MRunnerLogic
#

class MRunnerLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self):
        """
        Called when the logic class is instantiated. Can be used for initializing member variables.
        """
        ScriptedLoadableModuleLogic.__init__(self)

        self.logCallback = None
        self.resourcePath = None
        self.repo = None


    def setDefaultParameters(self, parameterNode):
        """
        Initialize parameter node with default settings.
        """
        if not parameterNode.GetParameter("Threshold"):
            parameterNode.SetParameter("Threshold", "100.0")
        if not parameterNode.GetParameter("Invert"):
            parameterNode.SetParameter("Invert", "false")


    def log(self, text):
        logging.info(text)
        if self.logCallback:
            self.logCallback(text)


    def logProcessOutput(self, proc):
        # Wait for the process to end and forward output to the log
        from subprocess import CalledProcessError
        while True:
            try:
                line = proc.stdout.readline()
            except UnicodeDecodeError as e:
                # Code page conversion happens because `universal_newlines=True` sets process output to text mode,
                # and it fails because probably system locale is not UTF8. We just ignore the error and discard the string,
                # as we only guarantee correct behavior if an UTF8 locale is used.
                pass
            if not line:
                break
            self.log(line.rstrip())
        proc.wait()
        retcode = proc.returncode
        if retcode != 0:
            raise CalledProcessError(retcode, proc.args, output=proc.stdout, stderr=proc.stderr)


    def setupPythonRequirements(self, upgrade=False):
        
        # install yaml python package
        needToInstallPackage = False
        try:
          import yaml
        except ModuleNotFoundError as e:
           needToInstallPackage = True
        if needToInstallPackage:
           self.log('PyYaml is required. Installing...')
           slicer.util.pip_install('pyyaml')

        # install pandas python package
        needToInstallPackage = False
        try:
          import pandas
        except ModuleNotFoundError as e:
           needToInstallPackage = True
        if needToInstallPackage:
           self.log('Pandas is required. Installing...')
           slicer.util.pip_install('pandas')

        # install numpy python package
        needToInstallPackage = False
        try:
          import numpy
        except ModuleNotFoundError as e:
           needToInstallPackage = True
        if needToInstallPackage:
           self.log('Numpy is required. Installing...')
           slicer.util.pip_install('numpy')

    def downloadRepo(self):
        # raw-path using the docker-dev branch instead of main.
        repo_json_url = ""


    def addDockerPath(self):
        # FIXME: add /usr/local/bin where docker-credential-desktop is installed to PATH 
        if not '/usr/local/bin' in os.environ["PATH"]:
            self.log(f"Adding /usr/local/bin to PATH.")
            os.environ["PATH"] += os.pathsep + '/usr/local/bin'


    def getDockerExecutable(self, verbose=True):
        dockerExecPath = None
        if os.name == 'nt': 
            dockerExecPath = "docker" # for windows just set docker
        else:
            import shutil
            self.addDockerPath()
            dockerExecPath = shutil.which('docker')
        if verbose:
            self.log(f"Docker executable found at {dockerExecPath}" if dockerExecPath else "Docker executable not found.")
        return dockerExecPath


    def checkForDocker(self):
        """
        Docker is required on the system to be installed and running. This function gets the docker executable and calls docker info for detailed information on the docker installation. If docker is not installed, fetching the executable will fail on unix systems and return None (but not on windows).
        TODO: version requirements might be added after evaluation.

        > docker info --format '{{json .}}'
        """

        print("os: ", os.name)

        import subprocess, json        
        dockerExecPath = self.getDockerExecutable()
        
        if dockerExecPath is None:
            self.log("Docker executable not found in your system.\nPlease install docker to proceed.")
            return False

        # run docker version
        # command = [dockerExecPath, '--version']

        # run docker info        
        command =  [dockerExecPath, 'info']
        command += ['--format', '{{json .}}']

        try:
            docker_info = subprocess.check_output(command).decode('utf-8')
            docker_info = json.loads(docker_info)

            if "ServerErrors" in docker_info:
                self.log(f"Docker ServerError: {', '.join(docker_info['ServerErrors'])}")
                return False

        except json.decoder.JSONDecodeError as e:
            self.log("Docker is not installed in your system.\nPlease install docker to proceed.")
            return False
        except Exception as e:
            print(f"Unexpected exception when pulling docker info: {str(e)}")
            return False

        return True


    def checkImage(self, model, useGPU=False):
        """Search available docker images. Returns true if the image is available. 
           > docker images --format '{{.Repository}}:{{.Tag}}'
        """
        #
        import subprocess
        
        #
        dockerExecPath = self.getDockerExecutable()
        assert dockerExecPath is not None, "DockerExecPath is None."

        #
        command =  [dockerExecPath, 'images']
        command += ['--format', '{{.Repository}}:{{.Tag}}']

        # get list of images
        images_lst = subprocess.check_output(command).decode('utf-8').split("\n")

        # search image
        image_ref =  model.getDockerfile().getImageRef(useGPU=useGPU) # image_name:image_tag

        #
        return image_ref in images_lst


    def pullImage(self, model, useGPU = False):
        """Pull image from docker hub.
           > docker pull [OPTIONS] NAME[:TAG|@DIGEST]
        """

        #
        import subprocess
        
        #
        dockerExecPath = self.getDockerExecutable()
        assert dockerExecPath is not None, "DockerExecPath is None."

        #
        image_ref = model.getDockerfile().getImageRef(useGPU=useGPU)
        command =  [dockerExecPath, 'pull', image_ref]

        # run command
        self.log("Running " + " ".join(command))
        proc = slicer.util.launchConsoleProcess(command)
        self.logProcessOutput(proc)
        self.log("Image pulled.")


    def downloadDockerfile(self, model, useGPU=False):
        """Downlaods the dockerfile from mhub repository to locally build image.
        """

        # get download url from repository definition
        dockerfile_url = model.getDockerfile().getDownloadPath(useGPU)

        # create temp folder 
        dockerfile_dir = slicer.util.tempDirectory()

        # download file 
        import urllib
        urllib.request.urlretrieve(dockerfile_url, os.path.join(dockerfile_dir, "Dockerfile"))

        #
        self.log(f"Dockerfile downloaded to {dockerfile_dir}")
        return dockerfile_dir


    def buildImage(self, model, downloadDockerfile=True, noCache=False, useGPU=False):
        """ Build a image locally.
            > docker build -t NAME[:TAG|@DIGEST] --build-arg USER_ID=1001 --build-arg GROUP_ID=1001 --platform linux/amd64 [--no-cache]
        """

        # download dockerfile
        dockerDir = self.downloadDockerfile(model, useGPU=useGPU)

        if not os.path.isdir(dockerDir):
            # TODO: handle error in calling methods
            raise FileNotFoundError(f"Cannot build image. Dockerfile for '{model.getName()} ({model.getDockerfile().getImageRef(useGPU=useGPU)})' not found at specified location '{dockerDir}'.")

        # prepare docker build command
        dockerExecPath = self.getDockerExecutable()
        assert dockerExecPath is not None, "DockerExecPath is None."

        command =  [dockerExecPath, 'build']
        command += ['-t', model.getDockerfile().getImageRef(useGPU=useGPU)]
        command += ['--build-arg', 'USER_ID=1001']
        command += ['--build-arg', 'GROUP_ID=1001']
        command += ['--platform', 'linux/amd64']
        
        if noCache:
            command += ["--no-cache"]
       
        # TODO: for Mac with M1 add platform
        # command += ['--platform', 'linux/amd64']
        # TODO: for linux add local user and group id --> no longer needed in newer docker files.

        command += [dockerDir]

        # run command
        self.log("Running " + " ".join(command))
        proc = slicer.util.launchConsoleProcess(command)
        self.logProcessOutput(proc)
        self.log("Image build.")


    def runContainerSync(self, model, dir, useGPU=False, containerArguments=None):
        """ Create and run a container of the specified image.
            NOTE: This code is blocking.
        """
        #
        dockerExecPath = self.getDockerExecutable()
        assert dockerExecPath is not None, "DockerExecPath is None."
        
        #
        command  = [dockerExecPath, "run", "--rm"]
        command += ["--volume", f"{dir}:/app/data/input_data"]
        command += ["--volume", f"{dir}:/app/data/output_data"]

        if useGPU:
            command += ["--gpus", "all"]

        # image to create container from
        command += [model.getDockerfile().getImageRef(useGPU=useGPU)]

        # slcier entrypoint
        mhub_model_dir = model.getName().lower()
        command += ["python3", f"/app/mhub/{mhub_model_dir}/scripts/slicer_run.py"]

        # commands
        if isinstance(containerArguments, list) and len(containerArguments) > 0:
            command += containerArguments

        # run
        self.log("Running " + " ".join(command))
        proc = slicer.util.launchConsoleProcess(command)
        self.logProcessOutput(proc)


    def displaySegmentation(self, outputSegmentation, dir, model):

        # clear output segmentation
        outputSegmentation.GetSegmentation().RemoveAllSegments()

        # iterate all output files from the repo
        ofs = model.getOutputFiles()
        for of in ofs:
            fileName = of.getFileName()

            # iterate all labels within file
            ofls = of.getLabels()
            for ofl in ofls:
                segment = ofl.getSegment()
                segmentName = segment.getName()
                segmentRGB = segment.getColor().getComponentsAsFloat()
                labelValue = ofl.getID()

                self.log(f"Importing {segmentName} (label: {labelValue}, file: {fileName})")

                #
                segmentPath = os.path.join(dir, fileName)
                assert os.path.isfile(segmentPath), f"Segment file not found at {segmentPath}."

                # create a label volume node and configure it
                segmentName = segment.getName()
                labelmapVolumeNode = slicer.util.loadLabelVolume(segmentPath, {"name": segmentName})

                # add segment
                segmentId = outputSegmentation.GetSegmentation().AddEmptySegment(segmentName, segmentName, segmentRGB)
                updatedSegmentIds = vtk.vtkStringArray()
                updatedSegmentIds.InsertNextValue(segmentId)
                
                # add the label volume node to the segmentation node and remove it
                slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(labelmapVolumeNode, outputSegmentation, updatedSegmentIds)
                #self.setTerminology(outputSegmentation, segmentName, segmentId)
                slicer.mrmlScene.RemoveNode(labelmapVolumeNode)


    def process(self, model, inputVolume, outputSegmentation, imageThreshold, downloadDockerfile=True, useGPU=False, noCache=False):
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputVolume: volume to be thresholded
        :param outputVolume: thresholding result
        :param imageThreshold: values above/below this threshold will be set to 0
        :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
        :param showResult: show output volume in slice viewers
        """

        if not inputVolume:
            raise ValueError("Input volume is invalid")

        import time, os
        startTime = time.time()
        self.log('Processing started')

        # create a temp directory icer
        tempDir = slicer.util.tempDirectory()

        # input file
        # TODO: rename to input.nrrd (requires update in aimi_alpha)
        inputFile = os.path.join(tempDir, "image.nrrd")

        # write selected input volume to temp directory
        volumeStorageNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLVolumeArchetypeStorageNode")
        volumeStorageNode.SetFileName(inputFile)
        volumeStorageNode.UseCompressionOff()
        volumeStorageNode.WriteData(inputVolume)
        volumeStorageNode.UnRegister(None)

        # image to run
        #image_tag = 'aimi/totalsegmentator:latest' # 'aimi/thresholder' # 'leo/thresholder'

        # check / build image
        if not self.checkImage(model, useGPU=useGPU) or noCache:

            # download dockerfile and build image locally if download opion is enabled
            if downloadDockerfile:
                self.buildImage(model, downloadDockerfile=downloadDockerfile, noCache=noCache, useGPU=useGPU)
            
            # if not, just pull the image from dockerhub
            else:
                self.pullImage(model, useGPU=useGPU)

        # run container
        self.runContainerSync(model, tempDir, useGPU=useGPU)

        # display segmentation
        self.displaySegmentation(outputSegmentation, tempDir, model)

        stopTime = time.time()
        self.log(f'Processing completed in {stopTime-startTime:.2f} seconds x')


#
# MRunnerTest
#

class MRunnerTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_MRunner1()

    def test_MRunner1(self):
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
        inputVolume = SampleData.downloadSample('MRunner1')
        self.delayDisplay('Loaded test data set')

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        threshold = 100

        # Test the module logic

        logic = MRunnerLogic()

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
