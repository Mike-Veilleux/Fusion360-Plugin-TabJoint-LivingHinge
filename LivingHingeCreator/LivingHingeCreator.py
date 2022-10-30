# Assuming you have not changed the general structure of the template no modification is needed in this file.
# from . import commands
# from .lib import fusion360utils as futil

import math, adsk.core, adsk.fusion, adsk.cam, traceback, csv, os.path

# Global list to keep all event handlers in scope.
# This is only needed with Python.
handlers = []

app = adsk.core.Application.cast(None)
sketch = adsk.fusion.Sketch.cast(None)
ui = adsk.core.UserInterface.cast(None)
pref = None

class PrefLattice:
    def __init__(self):
        self.SmartFit = False
        self.OverShoot = False
        self.Flip180 = False
        self.Link = 3
        self.Lattice = 20


    def ReadPref(self):
        isFileExisting: bool = os.path.isfile('LivingHingeCreator.pref')

        if not isFileExisting:
            csv_columns = ['SmartFit',
                           'OverShoot',
                           'Flip180',
                           'Link',
                           'Lattice']

            dict_data = [{'SmartFit': self.SmartFit,
                          'OverShoot': self.OverShoot,
                          'Flip180': self.Flip180,
                          'Link': self.Link,
                          'Lattice': self.Lattice}]

            csv_file = "LivingHingeCreator.pref"

            try:
                with open(csv_file, 'w') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
                    writer.writeheader()
                    for data in dict_data:
                        writer.writerow(data)
            except IOError:
                print("I/O error")

        else:
            input_file = csv.DictReader(open("LivingHingeCreator.pref"))

            # use enumerate to generate row indices, and break the loop when the index reaches your target:
            # https: // stackoverflow.com / questions / 53340694 / csv - dictreader - only - read - in -certain - rows

            for i, row in enumerate(input_file):
                if i == 0:
                    self.SmartFit = row["SmartFit"]
                    self.OverShoot = row["OverShoot"]
                    self.Flip180 = row["Flip180"]
                    self.Link = row["Link"]
                    self.Lattice = row["Lattice"]
                else:
                    break



    def WritePref(self):
        csv_columns = ['SmartFit',
                       'OverShoot',
                       'Flip180',
                       'Link',
                       'Lattice']

        dict_data = [{'SmartFit': self.SmartFit,
                      'OverShoot': self.OverShoot,
                      'Flip180': self.Flip180,
                      'Link': self.Link,
                      'Lattice': self.Lattice}]

        csv_file = "LivingHingeCreator.pref"

        try:
            with open(csv_file, 'w') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
                writer.writeheader()
                for data in dict_data:
                    writer.writerow(data)
        except IOError:
            print("I/O error")





def run(context):
    try:
        global app, ui, pref
        app = adsk.core.Application.get()
        # sketch = adsk.fusion.Sketch.cast(app.activeEditObject)
        # lines = sketch.sketchCurves.sketchLines
        ui = app.userInterface
        pref = PrefLattice()

        # Get the CommandDefinitions collection.
        cmdDefs = ui.commandDefinitions

        # Create a button command definition.
        buttonLivingHinge = cmdDefs.addButtonDefinition('CreateLivingHingeID',
                                                    'Create Living Hinge',
                                                    'Use sketch line to create a living hinge...'
                                                    ,
                                                    './/Resources//Sample')  # comment Resourse argument out for script Mode.

        buttonLivingHinge.tooltip = 'Modify a selected sketch line into a living hinge pattern'
        buttonLivingHinge.toolClipFilename = './/Resources//Sample//LivingHingeCreatorToolTipImage.png'

        # Connect to the command created event.
        LivingHingeCommandCreated = LivingHingeCommandCreatedEventHandler()
        buttonLivingHinge.commandCreated.add(LivingHingeCommandCreated)
        handlers.append(LivingHingeCommandCreated)

        # Get the "DESIGN" workspace.
        designWS = ui.workspaces.itemById('FusionSolidEnvironment')


        # Get the "ADD-INS" panel from the "DESIGN" workspace.
        addInsPanel = designWS.toolbarPanels.itemById('SketchModifyPanel')
        # addInsPanel = designWS.toolbarPanels.itemById('SolidScriptsAddinsPanel')

        # Add the button to the bottom of panel.
        buttonControl = addInsPanel.controls.addCommand(buttonLivingHinge)

        # Make the button available in the panel.
        buttonControl.isPromotedByDefault = True
        buttonControl.isPromoted = True


        # This will run the start function in each of your commands as defined in commands/__init__.py
        # commands.start()

        adsk.autoTerminate(False)


    except:

        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))



class LivingHingeCommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
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

        # Not sure what this does?
        # app = adsk.core.Application.get()
        des = adsk.fusion.Design.cast(app.activeProduct)

        # -------------------------------------------
        # Initialize Preference settings
        # -------------------------------------------
        pref.ReadPref()


        # Define inputs
        lineSelDef = inputs.addSelectionInput('lisel', 'Line', 'Select line')
        lineSelDef.addSelectionFilter('SketchLines')
        lineSelDef.setSelectionLimits(2)
        lineSelDef.isFullWidth = False


        if pref.Flip180 == "True":
            flipLineDef = inputs.addBoolValueInput('flipLineID', 'Flip 180°', True, '', True)
        else:
            flipLineDef = inputs.addBoolValueInput('flipLineID', 'Flip 180°', True, '', False)


        if pref.SmartFit == 'True':
            skewedLineDef = inputs.addBoolValueInput('skewedLineID', 'Smart Fit', True, '', True)
        else:
            skewedLineDef = inputs.addBoolValueInput('skewedLineID', 'Smart Fit', True, '', False)


        if pref.OverShoot == "True":
            overshootLineDef = inputs.addBoolValueInput('overshootLineID', 'Overshoot', True, '', True)
        else:
            overshootLineDef = inputs.addBoolValueInput('overshootLineID', 'Overshoot', True, '', False)

        # skewedLineDef = inputs.addBoolValueInput('skewedLineID', 'Smart Fit', True, '')
        # overshootLineDef = inputs.addBoolValueInput('overshootLineID', 'Overshoot', True, '')
        # flipLineDef = inputs.addBoolValueInput('flipLineID', 'Flip 180°', True, '')


        linkfDef = inputs.addFloatSpinnerCommandInput('linkID', 'Link', 'mm', 0.00, 100, 1, float(pref.Link))
        latticefDef = inputs.addFloatSpinnerCommandInput('latticeID', 'Lattice', 'mm', 0.00, 1000, 1, float(pref.Lattice))

        onExecute = LivingHingeCommandExecuteHandler()
        cmd.execute.add(onExecute)
        handlers.append(onExecute)

        onExecutePreview = LivingHingeCommandExecutePreviewHandler()
        cmd.executePreview.add(onExecutePreview)
        handlers.append(onExecutePreview)





class LivingHingeCommandExecutePreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)
            inputs = eventArgs.command.commandInputs

            # Get var from inputs Container

            latticeWidthPrefrered = inputs.itemById('latticeID').value
            linkSize = inputs.itemById('linkID').value
            isOvershooting = inputs.itemById('overshootLineID').value
            isFlipped = inputs.itemById('flipLineID').value
            isSkewed = inputs.itemById('skewedLineID').value

            # Safe way to iterate through input collection set => from Adsk website
            lines = []
            selLineNb = inputs.itemById('lisel').selectionCount
            for i in range(0, int(selLineNb)):
                lines.append(inputs.itemById('lisel').selection(i).entity)

                # -------------------------------------------
                # Initialize Preference settings for Writing
                # -------------------------------------------
                # pref = Pref()
                pref.SmartFit = isSkewed
                pref.OverShoot = isOvershooting
                pref.Flip180 = isFlipped
                pref.Link = linkSize * 10
                pref.Lattice = latticeWidthPrefrered * 10
                pref.WritePref()

            # Call def for run!
            if len(lines) >=2:
                CreateLattice(lines, latticeWidthPrefrered, linkSize, isOvershooting, isFlipped, isSkewed)



        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))





class LivingHingeCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        import math
        eventArgs = adsk.core.CommandEventArgs.cast(args)

        # Get the values from the command inputs.
        inputs = eventArgs.command.commandInputs

        # Get var from inputs Container
        latticeWidthPrefrered = inputs.itemById('latticeID').value
        linkSize = inputs.itemById('linkID').value
        isOvershooting = inputs.itemById('overshootLineID').value
        isFlipped = inputs.itemById('flipLineID').value
        isSkewed = inputs.itemById('skewedLineID').value

        # Safe way to iterate through input collection set => from Adsk website
        lines = []
        selLineNb = inputs.itemById('lisel').selectionCount
        for i in range(0, int(selLineNb)):
            lines.append(inputs.itemById('lisel').selection(i).entity)

        # -------------------------------------------
        # Initialize Preference settings for Writing
        # -------------------------------------------
        # pref = Pref()
        pref.SmartFit = isSkewed
        pref.OverShoot = isOvershooting
        pref.Flip180 = isFlipped
        pref.Link = linkSize * 10
        pref.Lattice = latticeWidthPrefrered * 10
        pref.WritePref()


        # Call def for run!
        if len(lines) >= 2:
            CreateLattice(lines, latticeWidthPrefrered, linkSize, isOvershooting, isFlipped, isSkewed)
            lines[0].deleteMe()
            lines[1].deleteMe()







def CreateLattice(_lines, _latticeWidthPrefrered, _linkSize, _isOvershooting, _isFlipped, _isSkewed):
    sketch = adsk.fusion.Sketch.cast(app.activeEditObject)
    sketch.isComputeDeferred = True

    lines = sketch.sketchCurves.sketchLines

    latticeWidthPrefrered = _latticeWidthPrefrered
    linkSize = _linkSize
    isOvershooting = _isOvershooting
    isFlipped = _isFlipped

    line1 = _lines[0]
    line2 = _lines[1]
    StartPointSecondLine = adsk.core.Point3D.cast(line2.startSketchPoint.geometry)



    # ------------------------------------------
    #  Error check => min req for building pattern
    # ------------------------------------------

    checkMinSingleLatticeWidth = line1.length - (linkSize * 2)
    if latticeWidthPrefrered > checkMinSingleLatticeWidth:
        ShowError(latticeWidthPrefrered, linkSize, line1)
        return False



    if _isSkewed == True:
        StartPointSecondLine = adsk.core.Point3D.cast(line2.endSketchPoint.geometry)


    Angle = angle(line1)

    if isFlipped == True:
        OriginPoint = line1.endSketchPoint.geometry
        if Angle >= 180:
            Angle = Angle - 180
        else:
            Angle = Angle + 180
    else:
        OriginPoint = line1.startSketchPoint.geometry

    patternLengthRAW = distanceBetweenPoint(line1.startSketchPoint.geometry, StartPointSecondLine)

    linkEdgeSize = linkSize / 2
    latticeBlockWidth = latticeWidthPrefrered + linkSize

    blockRepMod = line1.length % latticeBlockWidth
    blockRep = (line1.length - blockRepMod) / latticeBlockWidth
    latticeWidth = latticeWidthPrefrered + (blockRepMod / blockRep)

    IntervalRepMod = patternLengthRAW % (linkSize * 2)
    IntervalRep = (patternLengthRAW - IntervalRepMod) / (linkSize * 2)

    if isOvershooting == True:
        IntervalRep += 1
        offsetDistance = ((linkSize * 2) - IntervalRepMod) / 2
        StartPoint = NextPoint(OriginPoint, Angle - 90, offsetDistance)

    if isOvershooting == False:
        offsetDistance = IntervalRepMod / 2
        StartPoint = NextPoint(OriginPoint, Angle + 90, offsetDistance)



    # loop Interval Drawing

    NextIntervalStartPt = DrawInterval(lines, StartPoint, blockRep, latticeWidth, linkSize, Angle)
    for x in range(1, int(IntervalRep)):
        NextIntervalStartPt = DrawInterval(lines, NextIntervalStartPt, blockRep, latticeWidth, linkSize, Angle)

    DrawIntervalEnd(lines, NextIntervalStartPt, blockRep, latticeWidth, linkSize, Angle)

    sketch.isComputeDeferred = False



def angle(_line):
    ptStart = _line.startSketchPoint
    ptEnd = _line.endSketchPoint
    roundingPrecision = 6

    angle = round(
        math.atan2(ptEnd.geometry.y - ptStart.geometry.y, ptEnd.geometry.x - ptStart.geometry.x) * 180 / math.pi,
        roundingPrecision)

    # Correction for angle if the angle goes above 180 deg in fusion => eg.: 190 = -170
    if angle < 0:
        angle = 180 + (angle + 180)

    return angle



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



def DrawIntervalEnd(_lines,_startPoint, _rep, _lattice, _link, _angle):
    sketchLines: adsk.fusion.Sketch.sketchCurves = _lines
    lastLine: adsk.fusion.SketchLine

    lastPoint = NextPoint(_startPoint, _angle, _link / 2)
    for x in range(0, int(_rep)):
        lastLine = sketchLines.addByTwoPoints(lastPoint, NextPoint(lastPoint, _angle, _lattice))
        lastPoint = NextPoint(lastLine.endSketchPoint.geometry, _angle, _link)

    return NextPoint(_startPoint, _angle + 90, _link)



def DrawIntervalMid(_lines,_startPoint, _rep, _lattice, _link, _angle):
    sketchLines: adsk.fusion.Sketch.sketchCurves = _lines
    lastLine: adsk.fusion.SketchLine

    # Half start
    lastLine = sketchLines.addByTwoPoints(_startPoint, NextPoint(_startPoint, _angle, (_lattice / 2)))
    lastPoint = NextPoint(lastLine.endSketchPoint.geometry, _angle, _link)

    # Middle filling
    for x in range(1, int(_rep)):
        lastLine = sketchLines.addByTwoPoints(lastPoint, NextPoint(lastPoint, _angle, _lattice))
        lastPoint = NextPoint(lastLine.endSketchPoint.geometry, _angle, _link)

    # half End
    lastLine = sketchLines.addByTwoPoints(lastPoint, NextPoint(lastPoint, _angle, (_lattice / 2)))

    return NextPoint(_startPoint, _angle + 90, _link )



def DrawInterval(_lines,_startPoint, _rep, _lattice, _link, _angle):

    lastPoint = DrawIntervalEnd(_lines, _startPoint, _rep, _lattice, _link, _angle)

    return DrawIntervalMid(_lines,lastPoint, _rep, _lattice, _link, _angle)


def ShowError(_checkMaxLatticeLength, _linkSize, _line):
    checkMaxLatticeLength = float(_checkMaxLatticeLength)
    linkSize = float(_linkSize)
    line = adsk.fusion.SketchLine.cast(_line)

    # app = adsk.core.Application.get()
    ui_error = app.userInterface
    str_NewLine = '\n'
    str_RefWidth = str(round(line.length * 10, 1))
    str_LatticeLength = str(checkMaxLatticeLength * 10)
    str_LinkSize = str(round(_linkSize * 10, 1))
    str_TotalLinksAndLattice = str(checkMaxLatticeLength * 10 + (2 * round(_linkSize * 10, 1)))


    str1 = 'The given values for the Links and Lattice are too big for this pattern witdh... '
    str2 = str_NewLine
    str3 = str_NewLine
    str4 = ' Selected reference line value = '
    str5 = str_RefWidth
    str6 = ' mm.'
    str7 = str_NewLine
    str8 = str_NewLine
    str9 = 'Current value for => Link + Lattice + Link  = '
    str10 = str_TotalLinksAndLattice
    str11 = ' mm.'
    str12 = str_NewLine
    str13 = str_NewLine
    str14 = 'Lower the Link or Lattice value!'
    str15 = str1 + str2 + str3 + str4 + str5 + str6 + str7 + str8 + str9 + str10 + str11 + str12 + str13 + str14
    # ShowError(str9)
    # sys.exit('Cancelled')
    error = ui_error.messageBox(str15, 'Warning')





def stop(context):
    try:
        # Remove all of the event handlers your app has created
        #futil.clear_handlers()

        # This will run the start function in each of your commands as defined in commands/__init__.py
        # commands.stop()
        cmdDefs = ui.commandDefinitions

        # Delete the button definition.
        buttonTabJoin = ui.commandDefinitions.itemById('CreateLivingHingeID')
        if buttonTabJoin:
            buttonTabJoin.deleteMe()

        # Get the "DESIGN" workspace.
        designWS = ui.workspaces.itemById('FusionSolidEnvironment')

        # Get panel the control is in.
        addInsPanel = designWS.toolbarPanels.itemById('SketchModifyPanel')
        # addInsPanel = designWS.toolbarPanels.itemById('SolidScriptsAddinsPanel')

        # Get and delete the button control.
        buttonControl = addInsPanel.controls.itemById('CreateLivingHingeID')
        if buttonControl:
            buttonControl.deleteMe()


    except:

        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))