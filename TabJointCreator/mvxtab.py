import math, adsk.core, adsk.fusion, adsk.cam, traceback,csv, os.path

class Pref2File:
    def __init__(self):
        self.Type = 'Male'
        self.Flip = 'False'
        self.KeepSelectedLines = 'False'
        self.UnitLength = 6
        self.MaterialThickness = 3
        self.Kerf = 200


    def ReadPref(self):
        isFileExisting: bool = os.path.isfile('TabJointCreator.pref')

        if not isFileExisting:
            csv_columns = ['Type',
                           'Flip',
                           'KeepSelectedLines',
                           'UnitLength',
                           'MaterialThickness',
                           'Kerf']

            dict_data = [{'Type': self.Type,
                          'Flip': self.Flip,
                          'KeepSelectedLines': self.KeepSelectedLines,
                          'UnitLength': self.UnitLength,
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
                    self.UnitLength = row["UnitLength"]
                    self.MaterialThickness = row["MaterialThickness"]
                    self.Kerf = row["Kerf"]
                else:
                    break



    def WritePref(self):
        csv_columns = ['Type',
                       'Flip',
                       'KeepSelectedLines',
                       'UnitLength',
                       'MaterialThickness',
                       'Kerf']

        dict_data = [{'Type': self.Type,
                      'Flip': self.Flip,
                      'KeepSelectedLines': self.KeepSelectedLines,
                      'UnitLength': self.UnitLength,
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


def CreateTabJoint(_unitLength, _materialThickness, _line, _flipLine , _keepSelectedLines, _kerf, _tabType, _isPreviewModel):

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
        ptStart = line.startSketchPoint
        ptEnd = line.endSketchPoint
    else:
        ptStart = line.endSketchPoint
        ptEnd = line.startSketchPoint




    # ------------------------------------------
    #  Define the angle of the line
    # ------------------------------------------

    angle = round(
        math.atan2(ptEnd.geometry.y - ptStart.geometry.y, ptEnd.geometry.x - ptStart.geometry.x) * 180 / math.pi,
        roundingPrecision)

    # Correction for angle if the angle goes above 180 deg in fusion => eg.: 190 = -170
    if angle < 0:
        angle = 180 + (angle + 180)




    # ------------------------------------------
    #  Data logic for method
    # ------------------------------------------

    # Define base data for method
    totalLength = round(line.length, roundingPrecision)
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
        ShowError(checkMinLength, materialThickness, line)
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

    lastLine = lines.addByTwoPoints(lastLine.endSketchPoint, ptEnd.geometry)




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

    lastLine = sketchLines.addByTwoPoints(_ptStart.geometry, NextPoint(_ptStart.geometry, angle, firstSegmentLength + (kerf / 2)))

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
                                          NextPoint(lastLine.endSketchPoint.geometry, angle + direction, materialThickness + kerf))
    lastLine = sketchLines.addByTwoPoints(lastLine.endSketchPoint,
                                          NextPoint(lastLine.endSketchPoint.geometry, angle, unitLength - (kerf * 2)))
    lastLine = sketchLines.addByTwoPoints(lastLine.endSketchPoint,
                                          NextPoint(lastLine.endSketchPoint.geometry, angle - direction, materialThickness + kerf))

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


#endregion




#region Error and Messaging

def ShowMyError(value):
    # app = adsk.core.Application.get()
    ui_error = app.userInterface
    val = str(value)
    ui_error.messageBox(val, 'Debuging Message')
    return True


def ShowError(_checkMinLength, _materialThickness, _line):
    checkMinLength = float(_checkMinLength)
    materialThickness = float(_materialThickness)
    line = adsk.fusion.SketchLine.cast(_line)

    # app = adsk.core.Application.get()
    ui_error = app.userInterface
    str1 = 'The selected line is only '
    str2 = str(round(line.length, 1))
    str3 = ' cm. The is not long enough for the minimal length requierement with a thickness of '
    str4 = str(materialThickness)
    str5 = ' cm.'
    str6 = 'Selectc a line of at least '
    str7 = str(checkMinLength)
    str8 = ' cm.'
    str9 = str1 + str2 + str3 + str4 + str5 + str6 + str7 + str8
    # ShowError(str9)
    # sys.exit('Cancelled')
    error = ui_error.messageBox(str9, 'Warning')

#endregion
