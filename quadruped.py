import maya.cmds as cmds
import base
import quadSpine
import backLeg
import frontLeg
import tail
import misc

reload(base)
reload(quadSpine)
reload(backLeg)
reload(frontLeg)
reload(tail)

class Quadruped(base.Base):
    def __init__(self, prefix, side='NA', id='standard'):
        base.Base.__init__(self, prefix, side, id)
        self.metaType = 'Quadruped'
        self.constructNameSpace(self.metaType)

    def setLocAttr(self, startPos=[0, 0, 0]):
        self.leftArm = frontLeg.FrontLeg(prefix=self.prefix, side='L', id='standard')
        self.rightArm = frontLeg.FrontLeg(prefix=self.prefix, side='R', id='standard')

        self.leftLeg = backLeg.BackLeg(prefix=self.prefix, side='L', id='standard')
        self.rightLeg = backLeg.BackLeg(prefix=self.prefix, side='R', id='standard')

        self.spine = quadSpine.QuadSpine(prefix=self.prefix, side='NA', id='spine')
        self.tail = tail.Tail(prefix=self.prefix, side='NA', id='tip')

        self.neckRoot = base.Base(prefix=self.prefix, side='NA', id='neckRoot')
        self.head = base.Base(prefix=self.prefix, side='NA', id='head')
        self.tip = base.Base(prefix=self.prefix, side='NA', id='tip')

        self.leftArm.setLocAttr(startPos=[1+startPos[0], 5+startPos[1], 3+startPos[2]])
        self.rightArm.setLocAttr(startPos=[-1+startPos[0], 5+startPos[1], 3+startPos[2]])
        self.leftLeg.setLocAttr(startPos=[1+startPos[0], 5+startPos[1], -3+startPos[2]])
        self.rightLeg.setLocAttr(startPos=[-1+startPos[0], 5+startPos[1], -3+startPos[2]])
        self.spine.setLocAttr(startPos=[startPos[0], 6+startPos[1], -3+startPos[2]])
        self.tail.setLocAttr(startPos=[startPos[0], 6+startPos[1], -4+startPos[2]])
        self.neckRoot.setLocAttr(startPos=[startPos[0], 6+startPos[1]+0.5, 3+startPos[2]+0.5])
        self.head.setLocAttr(startPos=[startPos[0], 7.5+startPos[1], 4+startPos[2]])
        self.tip.setLocAttr(startPos=[startPos[0], 7.5+startPos[1], 6+startPos[2]])

    def buildGuide(self):
        self.spine.buildGuide()
        self.leftArm.buildGuide()
        self.rightArm.buildGuide()
        self.leftLeg.buildGuide()
        self.rightLeg.buildGuide()
        self.tail.buildGuide()
        self.neckRoot.buildGuide()
        self.head.buildGuide()
        self.tip.buildGuide()

        cmds.rotate(90, 0, 0, self.head.loc)
        cmds.rotate(90, 0, 0, self.tip.loc)

    def constructJnt(self):
        leftShoulder = self.leftArm.constructJnt()
        rightShoulder = self.rightArm.constructJnt()
        leftHip = self.leftLeg.constructJnt()
        rightHip = self.rightLeg.constructJnt()
        spineRoot = self.spine.constructJnt()
        tailRoot = self.tail.constructJnt()

        neckRoot = self.neckRoot.constructJnt()
        head = self.head.constructJnt()
        tip = self.tip.constructJnt()

        # parent leg root joints to root spline joint
        misc.batchParent([leftShoulder, rightShoulder], self.spine.topSpine)

        # parent arm root joints to top spline joint
        misc.batchParent([leftHip, rightHip], spineRoot)

        # parent tail to spine
        cmds.parent(tailRoot, spineRoot)

        # parent neck, head, tip
        cmds.parent(neckRoot, self.spine.topSpine)
        cmds.parent(head, neckRoot)
        cmds.parent(tip, head)

    def placeCtrl(self):
        self.leftArm.placeCtrl()
        self.rightArm.placeCtrl()
        self.leftLeg.placeCtrl()
        self.rightLeg.placeCtrl()
        self.spine.placeCtrl()
        self.tail.placeCtrl()

        self.neckRoot.placeCtrl()
        self.head.placeCtrl()
        self.tip.placeCtrl()

        cmds.addAttr(self.spine.masterCtrl, longName='FK_IK', attributeType='double', defaultValue=1, minValue=0, maxValue=1, keyable=True)

    def addConstraint(self):
        self.leftArm.addConstraint()
        self.rightArm.addConstraint()
        self.leftLeg.addConstraint()
        self.rightLeg.addConstraint()

        self.tail.addConstraint()
        self.neckRoot.addConstraint()
        self.head.addConstraint()
        self.tip.addConstraint()
        self.spine.addConstraint()

        # parenting the front and back leg and tail under spine ctrl
        misc.batchParent([self.leftArm.shoulderCtrlOffset, self.rightArm.shoulderCtrlOffset], self.spine.topCtrl)
        misc.batchParent([self.leftLeg.hipCtrlOffset, self.rightLeg.hipCtrlOffset], self.spine.rootCtrl)
        cmds.parentConstraint(self.spine.rootCtrl, self.tail.masterCtrl, mo=True)

        # hide tail ctrl and connect ik/fk switch to spine master ctrl
        cmds.connectAttr(self.spine.masterCtrl+'.FK_IK', self.tail.masterCtrl+'.FK_IK')

        # parent head up
        cmds.parent(self.neckRoot.ctrlOffsetGrp, self.spine.topCtrl)
        cmds.parent(self.head.ctrlOffsetGrp, self.neckRoot.ctrl)
        cmds.parent(self.tip.ctrlOffsetGrp, self.head.ctrl)

    def colorCtrl(self):
        self.leftArm.colorCtrl()
        self.rightArm.colorCtrl()
        self.leftLeg.colorCtrl()
        self.rightLeg.colorCtrl()
        self.spine.colorCtrl()
        self.tail.colorCtrl()
        self.neckRoot.colorCtrl()
        self.head.colorCtrl()
        self.tip.colorCtrl()

    def deleteGuide(self):
        loc = cmds.ls(self.locGrp)
        cmds.delete(loc)

