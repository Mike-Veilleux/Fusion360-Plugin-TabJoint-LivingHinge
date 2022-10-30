import math, adsk.core, adsk.fusion, adsk.cam, traceback, csv, os.path

# Global list to keep all event handlers in scope.
# This is only needed with Python.
handlers = []

app = adsk.core.Application.cast(None)
ui = adsk.core.UserInterface.cast(None)
pref = None

def run(context):
    # ui = None
    try:
        global app, ui, pref
        app = adsk.core.Application.get()
        ui = app.userInterface
        pref = Pref()

        # Get the CommandDefinitions collection.
        cmdDefs = ui.commandDefinitions

        # Create a button command definition.
        buttonTabJoin = cmdDefs.addButtonDefinition('CreateTabJoinID',
                                                   'Create Tab Joint',
                                                   'Convert sketch line to tab joint...'
                                                    , './/Resources//Sample') # comment Resourse argument out for script Mode.

        buttonTabJoin.tooltip = 'Modify a selected sketch line into a tab joint pattern'
        buttonTabJoin.toolClipFilename = './/Resources//Sample//TabJoinCreatorToolTipImage.png'

        # Connect to the command created event.
        tabJoinCommandCreated = TabJoinCommandCreatedEventHandler()
        buttonTabJoin.commandCreated.add(tabJoinCommandCreated)
        handlers.append(tabJoinCommandCreated)

        # Get the "DESIGN" workspace.
        designWS = ui.workspaces.itemById('FusionSolidEnvironment')

        # Get the "ADD-INS" panel from the "DESIGN" workspace.
        addInsPanel = designWS.toolbarPanels.itemById('SketchModifyPanel')
        # addInsPanel = designWS.toolbarPanels.itemById('SolidScriptsAddinsPanel')


        # Add the button to the bottom of panel.
        buttonControl = addInsPanel.controls.addCommand(buttonTabJoin)

        # Make the button available in the panel.
        buttonControl.isPromotedByDefault = True
        buttonControl.isPromoted = True



        # Execute the command on loaded => usefull when running in Script mode and not in Addin Mode.
        #buttonTabJoin.execute()

        # Keep the script running.
        adsk.autoTerminate(False)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))




#region Addin Handlers


class TabJoinCommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        # Verify that a sketch is active.
        # app = adsk.core.Application.get()
        if app.activeEditObject.objectType != adsk.fusion.Sketch.classType():
            ui = app.userInterface
            ui.messageBox('A sketch must be active for this command.')
            return False

        eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)

        # Get the command
        cmd = eventArgs.command

        # Get the CommandInputs collection to create new command inputs.
        inputs = cmd.commandInputs



        #Not sure what this does?
        # app = adsk.core.Application.get()
        des = adsk.fusion.Design.cast(app.activeProduct)

        #-------------------------------------------
        #Initialize Preference settings
        # -------------------------------------------
        pref.ReadPref()

        # Define inputs
        lineSelDef = inputs.addSelectionInput('lisel', 'Line', 'Select line')
        lineSelDef.addSelectionFilter('SketchLines')
        lineSelDef.setSelectionLimits(0)
        lineSelDef.isFullWidth = False



        tabTypeDropDownDef = inputs.addDropDownCommandInput('tabTypeDropDownID', 'Tab Type', adsk.core.DropDownStyles.LabeledIconDropDownStyle)
        radioButtonItems = tabTypeDropDownDef.listItems
        if pref.Type == 'Male':
            radioButtonItems.add('Male', True)
            radioButtonItems.add('Female', False)
        else:
            radioButtonItems.add('Male', False)
            radioButtonItems.add('Female', True)



        if pref.Flip == 'True':
            flipLineDef = inputs.addBoolValueInput('flipLineID', 'Flip Tab Side', True, '', True)
        else:
            flipLineDef = inputs.addBoolValueInput('flipLineID', 'Flip Tab Side', True, '', False)

        if pref.InnerFit == 'True':
            innerFitDef = inputs.addBoolValueInput('innerFitID', 'Is inner fit ', True, '', True)
        else:
            innerFitDef = inputs.addBoolValueInput('innerFitID', 'Is inner fit ', True, '', False)

        if pref.KeepSelectedLines == 'True':
            keepSelectedLinesDef = inputs.addBoolValueInput('keepSelectedLinesID', 'Keep Selected Lines',
                                                            True, '', True)
        else:
            keepSelectedLinesDef = inputs.addBoolValueInput('keepSelectedLinesID', 'Keep Selected Lines',
                                                            True, '', False)

        # flipLineDef = inputs.addBoolValueInput('flipLineID', 'Flip Tab Side', bool(pref.Flip), '', bool(pref.Flip))
        # keepSelectedLinesDef = inputs.addBoolValueInput('keepSelectedLinesID', 'Keep Selected Lines', bool(pref.KeepSelectedLines), '', bool(pref.KeepSelectedLines))

        materialThicknessDef = inputs.addFloatSpinnerCommandInput('mt', 'Material Thickness', 'mm', 0.0, 1000.0, 1.0, float(pref.MaterialThickness))

        kerfDef = inputs.addFloatSpinnerCommandInput('kerfID', 'Kerf', 'micron', 0.00, 5000, 50, float(pref.Kerf))


        # Connect to the execute event.

        # onInputChanged = TabJointCommandChangeHandler()
        # cmd.inputChanged.add(onInputChanged)
        # handlers.append(onInputChanged)


        onExecute = TabJointCommandExecuteHandler()
        cmd.execute.add(onExecute)
        handlers.append(onExecute)

        onExecutePreview = TabJointCommandExecutePreviewHandler()
        cmd.executePreview.add(onExecutePreview)
        handlers.append(onExecutePreview)


class TabJointCommandExecutePreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)
            inputs = eventArgs.command.commandInputs

            # Get var from inputs Container
            tabType = inputs.itemById('tabTypeDropDownID').selectedItem.name
            flipLine = inputs.itemById('flipLineID').value
            innerFit = inputs.itemById('innerFitID').value
            keepSelectedLines = inputs.itemById('keepSelectedLinesID').value
            materialThickness = inputs.itemById('mt').value
            kerf = inputs.itemById('kerfID').value



            # Safe way to iterate through input collection set => from Adsk website
            lines = []
            selLineNb = inputs.itemById('lisel').selectionCount
            for i in range(0, int(selLineNb)):
                lines.append(inputs.itemById('lisel').selection(i).entity)

            # -------------------------------------------
            # Initialize Preference settings for Writing
            # -------------------------------------------
            # pref = Pref()
            pref.Type = tabType
            pref.Flip = flipLine
            pref.InnerFit = innerFit
            pref.KeepSelectedLines = keepSelectedLines
            pref.MaterialThickness = materialThickness * 10
            pref.Kerf = kerf * 10000
            pref.WritePref()


            # -------------------------------------------
            # Let's do it!!!
            # -------------------------------------------
            ProcessAllLines(materialThickness, lines, flipLine, innerFit, keepSelectedLines, kerf, tabType, True)



        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))



class TabJointCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        import math
        eventArgs = adsk.core.CommandEventArgs.cast(args)

        # Get the values from the command inputs.
        inputs = eventArgs.command.commandInputs

        # Get var from inputs Container
        tabType = inputs.itemById('tabTypeDropDownID').selectedItem.name
        flipLine = inputs.itemById('flipLineID').value
        innerFit = inputs.itemById('innerFitID').value
        keepSelectedLines = inputs.itemById('keepSelectedLinesID').value
        materialThickness = inputs.itemById('mt').value
        kerf = inputs.itemById('kerfID').value

        # Safe way to iterate through input collection set => from Adsk website
        lines = []
        selLineNb = inputs.itemById('lisel').selectionCount
        for i in range(0, int(selLineNb)):
            lines.append(inputs.itemById('lisel').selection(i).entity)

        # -------------------------------------------
        # Initialize Preference settings for Writing
        # -------------------------------------------
        # pref = Pref()
        pref.Type = tabType
        pref.Flip = flipLine
        pref.InnerFit = innerFit
        pref.KeepSelectedLines = keepSelectedLines
        pref.MaterialThickness = materialThickness * 10
        pref.Kerf = kerf * 10000
        pref.WritePref()


        # -------------------------------------------
        # Let's do it!!!
        # -------------------------------------------
        ProcessAllLines(materialThickness, lines, flipLine, innerFit, keepSelectedLines, kerf, tabType, False)


#endregion




#region Main Methods


def ProcessAllLines(_materialThickness, _lines, _flipLine, _innerFit, _keepSelectedLines, _kerf, _tabType, _isPreviewModel):

    sketch = adsk.fusion.Sketch.cast(app.activeEditObject)
    sketch.isComputeDeferred = True

    # Loop each line in collection and create tabs
    for line in _lines:
        CreateTabJoint(_materialThickness, line, _flipLine, _innerFit, _keepSelectedLines, _kerf, _tabType, _isPreviewModel)

    sketch.isComputeDeferred = False



def CreateTabJoint(_materialThickness, _line, _flipLine, _innerFit , _keepSelectedLines, _kerf, _tabType, _isPreviewModel):

    sketch = adsk.fusion.Sketch.cast(app.activeEditObject)
    lines = sketch.sketchCurves.sketchLines
    lastLine = adsk.fusion.SketchLine

    roundingPrecision = 6
    tabType = _tabType
    kerf = round(float(_kerf / 2), roundingPrecision)
    materialThickness = round(float(_materialThickness), roundingPrecision)
    line = adsk.fusion.SketchLine.cast(_line)
    safeSide = materialThickness
    unitLength = round(materialThickness * 2, roundingPrecision)


    # ------------------------------------------
    #  Adjustment for which direction the like has being created
    # ------------------------------------------

    if not _flipLine:
        ptStart = line.startSketchPoint.geometry
        ptEnd = line.endSketchPoint.geometry
    else:
        ptStart = line.endSketchPoint.geometry
        ptEnd = line.startSketchPoint.geometry




    # ------------------------------------------
    #  Define the angle of the line
    # ------------------------------------------

    angle = round(
        math.atan2(ptEnd.y - ptStart.y, ptEnd.x - ptStart.x) * 180 / math.pi,
        roundingPrecision)

    # Correction for angle if the angle goes above 180 deg in fusion => eg.: 190 = -170
    if angle < 0:
        angle = 180 + (angle + 180)


    # ------------------------------------------
    #  INNER FIT => Adjust Start and End Points
    # ------------------------------------------

    if _innerFit:
        if angle >= 180:
            tmpAng = angle - 180
        else:
            tmpAng = angle + 180

        ptStart = NextPoint(ptStart, tmpAng, materialThickness )
        ptEnd = NextPoint(ptEnd, angle, materialThickness)



    # ------------------------------------------
    #  Data logic for method
    # ------------------------------------------

    # Define base data for method
    # totalLength = round(line.length, roundingPrecision)
    totalLength = distanceBetweenPoint(ptStart, ptEnd)
    grossPatternLength = totalLength - (safeSide * 2)
    grossPatternModulus = round(grossPatternLength % unitLength, roundingPrecision)
    netPatternLength = round(grossPatternLength - grossPatternModulus, roundingPrecision)
    units = round((netPatternLength / unitLength), roundingPrecision)

    # Find the number of repetitions and define => firstSegmentLength
    if units == 1:
        repetitions = -1
        firstSegmentLength = (grossPatternModulus / 2) + safeSide
    else:
        if units % 2 == 0:
            repetitions = int((units / 2) - 1)
            firstSegmentLength = (grossPatternModulus / 2) + safeSide + (unitLength / 2)
        else:
            repetitions = int((units - 1) / 2)
            firstSegmentLength = (grossPatternModulus / 2) + safeSide




    # ------------------------------------------
    #  Error check => min req for building pattern
    # ------------------------------------------

    checkMinLength = unitLength + (safeSide * 2)
    if totalLength <= checkMinLength:
        ShowError(checkMinLength, materialThickness, line, kerf)
        return False




    # ------------------------------------------
    #             Pattern Drawing
    # ------------------------------------------

    if _isPreviewModel:
        DrawSideMarker(line, angle, materialThickness, _tabType)

    lastLine = DrawFirstSegment(lines, ptStart, firstSegmentLength, angle, _kerf, _tabType)

    #Always start with a tab
    lastLine = DrawTab(lines, lastLine, unitLength, angle, materialThickness, kerf, tabType)

    for x in range(0, int(repetitions)):
        lastLine = DrawFlatTab(lines, lastLine, unitLength, angle, kerf, tabType)
        lastLine = DrawTab(lines, lastLine, unitLength, angle, materialThickness, kerf, tabType)

    lastLine = lines.addByTwoPoints(lastLine.endSketchPoint, ptEnd)




    # ------------------------------------------
    #             Method Closing
    # ------------------------------------------

    # Delete originally selected line if not for preview
    #if not _isPreviewModel:
     #   line.deleteMe()

    if not _keepSelectedLines and not _isPreviewModel:
        line.deleteMe()

    #Not sure what is that for => copy pasted from Adsk template
    return True

#endregion




#region Drawing Helper Methods

def DrawFirstSegment(_sketchLines, _ptStart, _firstSegmentLength, _angle, _kerf, _tabType):
    """Draw the first segment of the pattern.
    Length is adjusted according to arguments values.
    The KERF value will be defined according to this method's logic"""

    sketchLines: adsk.fusion.Sketch.sketchCurves = _sketchLines
    firstSegmentLength: float = _firstSegmentLength
    angle: float = _angle

    if _tabType == 'Male':
        kerf = -abs(_kerf)
    if _tabType == 'Female':
        kerf = _kerf

    lastLine = sketchLines.addByTwoPoints(_ptStart, NextPoint(_ptStart, angle, firstSegmentLength + (kerf / 2)))

    return lastLine


def DrawTab(_sketchLines, _lastLine, _unitLength, _angle, _materialThickness, _kerf, _tabType):
    sketchLines: adsk.fusion.Sketch.sketchCurves = _sketchLines
    lastLine: adsk.fusion.SketchLine = _lastLine
    unitLength: float = _unitLength
    angle: float = _angle
    materialThickness: float = _materialThickness

    if _tabType == 'Male':
        direction = -90
        kerf = -abs(_kerf)
    if _tabType == 'Female':
        direction = 90
        kerf = _kerf

    lastLine = sketchLines.addByTwoPoints(lastLine.endSketchPoint,
                                          NextPoint(lastLine.endSketchPoint.geometry, angle + direction, materialThickness - kerf))
    lastLine = sketchLines.addByTwoPoints(lastLine.endSketchPoint,
                                          NextPoint(lastLine.endSketchPoint.geometry, angle, unitLength - (kerf * 2)))
    lastLine = sketchLines.addByTwoPoints(lastLine.endSketchPoint,
                                          NextPoint(lastLine.endSketchPoint.geometry, angle - direction, materialThickness - kerf))

    return lastLine


def DrawFlatTab(_sketchLines, _lastLine, _unitLength, _angle, _kerf, _tabType):
    sketchLines: adsk.fusion.Sketch.sketchCurves = _sketchLines
    lastLine: adsk.fusion.SketchLine = _lastLine
    unitLength: float = _unitLength
    angle: float = _angle

    if _tabType == 'Male':
        kerf = -abs(_kerf)
    if _tabType == 'Female':
        kerf = _kerf

    lastLine = sketchLines.addByTwoPoints(lastLine.endSketchPoint, NextPoint(lastLine.endSketchPoint.geometry, angle, unitLength + (kerf * 2)))

    return lastLine


def DrawSideMarker(_lastLine, _angle, _materialThickness, _tabType):

    sketch = adsk.fusion.Sketch.cast(app.activeEditObject)
    lastLine = adsk.fusion.SketchLine.cast(_lastLine)
    lines = sketch.sketchCurves.sketchLines

    if _tabType == 'Male':
        direction = -90
        dirString = 'MALE Tab should be OUTSIDE the material'
        isAbove = True
    if _tabType == 'Female':
        direction = 90
        dirString = 'FEMALE Tab should be INSIDE the material'
        isAbove = False


    vDist = _materialThickness * 2

    hDistMid = adsk.core.Point3D.cast(None)
    hDistMid = adsk.core.Point3D.create((lastLine.endSketchPoint.geometry.x + lastLine.startSketchPoint.geometry.x) / 2,
                                        (lastLine.endSketchPoint.geometry.y + lastLine.startSketchPoint.geometry.y) / 2,
                                        (lastLine.endSketchPoint.geometry.z + lastLine.startSketchPoint.geometry.z) / 2)


    # hDistPos = adsk.core.Point3D.cast(None)
    hDistPos = NextPoint(hDistMid, _angle + direction, vDist)

    underline = lines.addByTwoPoints(hDistPos, NextPoint(hDistPos, _angle, 0.01))

    texts = sketch.sketchTexts

    string = texts.createInput2(dirString, float(_materialThickness / 3))

    string.setAsAlongPath(underline, True, adsk.core.HorizontalAlignments.CenterHorizontalAlignment, 0)

    texts.add(string)



def distanceBetweenPoint(_pt1, _pt2):
    # ptStart1 = _line1.startSketchPoint.geometry
    # ptStart2 = _line2.startSketchPoint.geometry

    return math.sqrt(((_pt2.x - _pt1.x) ** 2) + ((_pt2.y - _pt1.y) ** 2))




def NextPoint(_p1, angle, distance):
    # If you are at point(x, y) and you want to move d unit in alpha
    # angle( in radian), then formula for destination point will be:
    #
    # xx = x + (d * cos(alpha))
    # yy = y + (d * sin(alpha))

    # Note: If angle is given in degree:
    # angle in radian = angle in degree * Pi / 180

    p1 = adsk.core.Point3D.cast(_p1)
    p2 = adsk.core.Point3D.create(p1.x + (distance * math.cos(angle * math.pi / 180)),
                                  p1.y + (distance * math.sin(angle * math.pi / 180)), 0.0)

    return p2


class Pref:
    def __init__(self):
        self.Type = 'Male'
        self.Flip = 'False'
        self.InnerFit = 'False'
        self.KeepSelectedLines = 'False'
        self.MaterialThickness = 3
        self.Kerf = 200


    def ReadPref(self):
        isFileExisting: bool = os.path.isfile('TabJointCreator.pref')

        if not isFileExisting:
            csv_columns = ['Type',
                           'Flip',
                           'InnerFit',
                           'KeepSelectedLines',
                           'MaterialThickness',
                           'Kerf']

            dict_data = [{'Type': self.Type,
                          'Flip': self.Flip,
                          'InnerFit': self.InnerFit,
                          'KeepSelectedLines': self.KeepSelectedLines,
                          'MaterialThickness': self.MaterialThickness,
                          'Kerf': self.Kerf}]

            csv_file = "TabJointCreator.pref"

            try:
                with open(csv_file, 'w') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
                    writer.writeheader()
                    for data in dict_data:
                        writer.writerow(data)
            except IOError:
                print("I/O error")

        else:
            input_file = csv.DictReader(open("TabJointCreator.pref"))

            # use enumerate to generate row indices, and break the loop when the index reaches your target:
            # https: // stackoverflow.com / questions / 53340694 / csv - dictreader - only - read - in -certain - rows

            for i, row in enumerate(input_file):
                if i == 0:
                    self.Type = row["Type"]
                    self.Flip = row["Flip"]
                    self.KeepSelectedLines = row["KeepSelectedLines"]
                    self.MaterialThickness = row["MaterialThickness"]
                    self.Kerf = row["Kerf"]
                else:
                    break



    def WritePref(self):
        csv_columns = ['Type',
                       'Flip',
                       'InnerFit',
                       'KeepSelectedLines',
                       'MaterialThickness',
                       'Kerf']

        dict_data = [{'Type': self.Type,
                      'Flip': self.Flip,
                      'InnerFit': self.InnerFit,
                      'KeepSelectedLines': self.KeepSelectedLines,
                      'MaterialThickness': self.MaterialThickness,
                      'Kerf': self.Kerf}]

        csv_file = "TabJointCreator.pref"

        try:
            with open(csv_file, 'w') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
                writer.writeheader()
                for data in dict_data:
                    writer.writerow(data)
        except IOError:
            print("I/O error")


#endregion




#region Error and Messaging

def ShowMyError(value):
    # app = adsk.core.Application.get()
    ui_error = app.userInterface
    val = str(value)
    ui_error.messageBox(val, 'Debuging Message')
    return True


def ShowError(_checkMinLength, _materialThickness, _line, _kerf):
    checkMinLength = float(_checkMinLength)
    materialThickness = float(_materialThickness)
    line = adsk.fusion.SketchLine.cast(_line)

    str_NewLine = '\n'
    str_RefLine = str(round(line.length * 10, 1))
    str_MatThickness = str(materialThickness * 10)
    str_MinLengthRequiered = str(((_kerf * 2) + checkMinLength) * 10)


    # app = adsk.core.Application.get()
    ui_error = app.userInterface
    str1 = 'The selected reference line is too short for generating the tab pattern...'
    str2 = str_NewLine
    str3 = str_NewLine
    str4 = 'Selected reference line length => '
    str5 = str_RefLine
    str6 = ' mm.'
    str7 = str_NewLine
    str8 = str_NewLine
    str9 = 'The minimum length for the current value settings is at least => '
    str10 = str_MinLengthRequiered
    str11 = ' mm.'
    str12 = str1 + str2 + str3 + str4 + str5 + str6 + str7 + str8 + str9 + str10 + str11
    # ShowError(str9)
    # sys.exit('Cancelled')
    error = ui_error.messageBox(str12, 'Warning')

#endregion







def stop(context):
    try:
        # app = adsk.core.Application.get()
        # ui = app.userInterface

        # # Delete the command definition.
        # cmdDef = ui.commandDefinitions.itemById('CreateTabJoinID')
        # if cmdDef:
        #     cmdDef.deleteMe()

        cmdDefs = ui.commandDefinitions

        # Delete the button definition.
        buttonTabJoin = ui.commandDefinitions.itemById('CreateTabJoinID')
        if buttonTabJoin:
            buttonTabJoin.deleteMe()

        # Get the "DESIGN" workspace.
        designWS = ui.workspaces.itemById('FusionSolidEnvironment')

        # Get panel the control is in.
        addInsPanel = designWS.toolbarPanels.itemById('SketchModifyPanel')
        # addInsPanel = designWS.toolbarPanels.itemById('SolidScriptsAddinsPanel')

        # Get and delete the button control.
        buttonControl = addInsPanel.controls.itemById('CreateTabJoinID')
        if buttonControl:
            buttonControl.deleteMe()



    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
