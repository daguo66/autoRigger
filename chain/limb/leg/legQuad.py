import maya.cmds as cmds

from .... import util, shape
from ....base import bone
from ....utility.common import hierarchy
from ....utility.rigging import joint, transform
from ....utility.datatype import vector


ATTRS = {
    'flx': 'flex',
    'swv': 'swivel',
    'tap': 'tap',
    'tip': 'tip',
    'wr': 'wrist'
}


class LegQuad(bone.Bone):
    """
    Module for quadruped leg module
    """

    def __init__(self, side, name, distance=1.5, height=0.2, is_front=0):
        bone.Bone.__init__(self, side, name)
        self.is_front = is_front

        self.distance = distance
        self.height = height

        self.limb_components = ['hip', 'knee', 'ankle', 'paw', 'toe']
        if is_front:
            self.limb_components = ['shoulder', 'elbow', 'wrist', 'paw', 'toe']

        # name
        self.helpers = list()
        self.leg_ik = None
        self.foot_ik = None
        self.toe_ik = None
        self.helper_ik = None

    @bone.update_base_name
    def create_namespace(self):
        for component in self.limb_components:
            self.locs.append('{}{}_loc'.format(self.base_name, component))
            self.jnts.append('{}{}_jnt'.format(self.base_name, component))
            self.helpers.append('{}{}helper_jnt'.format(self.base_name, component))
            self.ctrls.append('{}{}_ctrl'.format(self.base_name, component))
            self.offsets.append('{}{}_offset'.format(self.base_name, component))

        self.leg_ik = '{}leg_ik'.format(self.base_name)
        self.foot_ik = '{}foot_ik'.format(self.base_name)
        self.toe_ik = '{}toe_ik'.format(self.base_name)
        self.helper_ik = '{}helper_ik'.format(self.base_name)

    def set_shape(self):
        self._shape = list(range(3))

        self._shape[0] = shape.make_sphere()
        self._shape[1] = shape.make_sphere()
        self._shape[2] = shape.make_circle()
        
    def create_locator(self):
        cmds.spaceLocator(n=self.locs[0])

        cmds.spaceLocator(n=self.locs[1])
        cmds.parent(self.locs[1], self.locs[0], r=1)
        
        if not self.is_front:
            cmds.move(0, -self.distance, 0, self.locs[1], r=1)
        else:
            cmds.move(0, -self.distance, -0.5 * self.distance, self.locs[1], r=1)

        cmds.spaceLocator(n=self.locs[2])
        cmds.parent(self.locs[2], self.locs[1], r=1)
        if not self.is_front:
            cmds.move(0, -self.distance, -0.5 * self.distance, self.locs[2], r=1)
        else:
            cmds.move(0, -self.distance, 0, self.locs[2], r=1)

        cmds.spaceLocator(n=self.locs[3])
        cmds.parent(self.locs[3], self.locs[2], r=1)
        if not self.is_front:
            cmds.move(0, -self.distance+self.height, 0, self.locs[3], r=1)
        else:
            cmds.move(0, -self.distance+self.height, 0.5 * self.distance, self.locs[3], r=1)

        cmds.spaceLocator(n=self.locs[4])
        cmds.parent(self.locs[4], self.locs[3], r=1)
        cmds.move(0, 0, 0.5 * self.distance, self.locs[4], r=1)

        cmds.parent(self.locs[0], util.G_LOC_GRP)
        return self.locs[0]

    def create_joint(self):
        # Result joint chain
        cmds.select(clear=1)
        for index in range(len(self.locs)):
            loc = cmds.ls(self.locs[index], transforms=1)
            loc_pos = cmds.xform(loc, q=1, t=1, ws=1)
            cmds.joint(p=loc_pos, n=self.jnts[index])

        joint.orient_joint(self.jnts[0])
        cmds.parent(self.jnts[0], util.G_JNT_GRP)

        if not self.is_front:
            # Helper joint chain
            cmds.select(clear=1)
            for index in range(len(self.locs[:-1])):
                loc = cmds.ls(self.locs[index], transforms=1)
                loc_pos = cmds.xform(loc, q=1, t=1, ws=1)
                cmds.joint(p=loc_pos, n=self.helpers[index])
    
            joint.orient_joint(self.helpers[0])
            cmds.parent(self.helpers[0], util.G_JNT_GRP)
            cmds.setAttr(self.helpers[0]+'.v', 0)

        return self.jnts[0]

    def place_controller(self):
        cmds.duplicate(self._shape[0], n=self.ctrls[0])
        cmds.group(em=1, n=self.offsets[0])
        transform.clear_transform(self.ctrls[0], self.offsets[0], self.jnts[0])

        # foot control
        cmds.duplicate(self._shape[2], n=self.ctrls[3])
        cmds.group(em=1, n=self.offsets[3])
        transform.clear_transform(self.ctrls[3], self.offsets[3], self.locs[3])

        # custom attribute for later pivot group access
        cmds.addAttr(self.ctrls[3], sn='flx', ln=ATTRS['flx'], at='double', k=1)
        cmds.addAttr(self.ctrls[3], sn='swv', ln=ATTRS['swv'], at='double', k=1)
        cmds.addAttr(self.ctrls[3], sn='tap', ln=ATTRS['tap'], at='double', k=1)
        cmds.addAttr(self.ctrls[3], sn='tip', ln=ATTRS['tip'], at='double', k=1)
        if self.is_front:
            cmds.addAttr(self.ctrls[3], sn='wr', ln=ATTRS['wr'], at='double', k=1)

        # Ankle control - poleVector
        pole_index = 1 if self.is_front else 2
        cmds.duplicate(self._shape[1], n=self.ctrls[pole_index])
        cmds.group(em=1, n=self.offsets[pole_index])
        transform.clear_transform(self.ctrls[pole_index], self.offsets[pole_index], self.jnts[pole_index])
        hierarchy.batch_parent(
            [self.offsets[0],
             self.offsets[3],
             self.offsets[pole_index]],
            util.G_CTRL_GRP
        )

    def build_ik(self):
        cmds.ikHandle(sj=self.jnts[0], ee=self.jnts[2], n=self.leg_ik, sol='ikRPsolver')
        cmds.ikHandle(sj=self.jnts[2], ee=self.jnts[3], n=self.foot_ik, sol='ikSCsolver')
        cmds.ikHandle(sj=self.jnts[3], ee=self.jnts[4], n=self.toe_ik, sol='ikSCsolver')
        cmds.setAttr(self.leg_ik+'.v', 0)
        cmds.setAttr(self.foot_ik+'.v', 0)
        cmds.setAttr(self.toe_ik+'.v', 0)

        if not self.is_front:
            cmds.ikHandle(sj=self.helpers[0], ee=self.helpers[3], n=self.helper_ik, sol='ikRPsolver')
            cmds.setAttr(self.helper_ik+'.v', 0)

    def add_measurement(self):
        hip_vec = vector.Vector(cmds.xform(self.jnts[0], q=1, ws=1, t=1))
        knee_vec = vector.Vector(cmds.xform(self.jnts[1], q=1, ws=1, t=1))
        ankle_vec = vector.Vector(cmds.xform(self.jnts[2], q=1, ws=1, t=1))
        foot_vec = vector.Vector(cmds.xform(self.jnts[3], q=1, ws=1, t=1))

        ankle_to_knee = (ankle_vec - knee_vec).length
        foot_to_ankle = (foot_vec - ankle_vec).length
        hip_to_knee = (knee_vec - hip_vec).length

        straighten_len = ankle_to_knee + hip_to_knee
        if not self.is_front:
            straighten_len += foot_to_ankle

        # create measurement
        if not self.is_front:
            measure_shape = cmds.distanceDimension(sp=hip_vec.as_list, ep=foot_vec.as_list)
        else:
            measure_shape = cmds.distanceDimension(sp=hip_vec.as_list, ep=ankle_vec.as_list)

        locs = cmds.listConnections(measure_shape)
        measure_node = cmds.listRelatives(measure_shape, parent=1, type='transform')
        length_node = '{}length_node'.format(self.base_name)
        hip_loc = '{}hip_node'.format(self.base_name)
        ankle_loc = '{}ankle_node'.format(self.base_name)
        cmds.rename(measure_node, length_node)
        cmds.rename(locs[0], hip_loc)
        cmds.rename(locs[1], ankle_loc)

        stretch_node = cmds.shadingNode('multiplyDivide', asUtility=1, n='{}stretch_node'.format(self.base_name))
        cmds.setAttr(stretch_node+'.operation', 2)
        cmds.setAttr(stretch_node+'.input2X', straighten_len)
        cmds.connectAttr(length_node+'.distance', stretch_node+'.input1X')

        condition_node = cmds.shadingNode('condition', asUtility=1, n='{}condition_node'.format(self.base_name))
        cmds.connectAttr(stretch_node+'.outputX', condition_node+'.firstTerm')
        cmds.setAttr(condition_node+'.secondTerm', 1)
        cmds.setAttr(condition_node+'.operation', 2)  # greater than
        cmds.connectAttr(stretch_node+'.outputX', condition_node+'.colorIfTrueR')
        cmds.setAttr(condition_node+'.colorIfFalseR', 1)

        if not self.is_front:
            for jnt in [self.jnts[0], self.jnts[1], self.jnts[2], self.helpers[0], self.helpers[1], self.helpers[2]]:
                cmds.connectAttr(condition_node+'.outColorR', jnt+'.sx')
        else:
            cmds.connectAttr(condition_node+'.outColorR', self.jnts[0]+'.sx')
            cmds.connectAttr(condition_node+'.outColorR', self.jnts[1]+'.sx')

        cmds.setAttr(length_node+'.v', 0)
        cmds.setAttr(hip_loc+'.v', 0)
        cmds.setAttr(ankle_loc+'.v', 0)
        hierarchy.batch_parent([length_node, hip_loc, ankle_loc], util.G_CTRL_GRP)

        cmds.parentConstraint(self.ctrls[0], hip_loc)
        cmds.parentConstraint(self.ctrls[3], ankle_loc, mo=1)

    def add_constraint(self):
        self.build_ik()

        # Shoulder pivot
        cmds.parentConstraint(self.ctrls[0], self.jnts[0])
        if not self.is_front:
            cmds.parentConstraint(self.ctrls[0], self.helpers[0])

        # Front foot pivot group
        toe_tap_pivot = cmds.group(em=1, n='{}toetap_pivot'.format(self.base_name))
        flex_pivot = cmds.group(em=1, n='{}flex_pivot'.format(self.base_name))
        swivel_pivot = cmds.group(em=1, n='{}swivel_pivot'.format(self.base_name))
        toe_tip_pivot = cmds.group(em=1, n='{}toetip_pivot'.format(self.base_name))

        wrist_pos = cmds.xform(self.jnts[2], q=1, ws=1, t=1)
        foot_pos = cmds.xform(self.jnts[3], q=1, ws=1, t=1)
        toe_pos = cmds.xform(self.jnts[4], q=1, ws=1, t=1)

        cmds.move(foot_pos[0], foot_pos[1], foot_pos[2], flex_pivot)
        cmds.move(foot_pos[0], foot_pos[1], foot_pos[2], toe_tap_pivot)
        cmds.move(foot_pos[0], foot_pos[1], foot_pos[2], swivel_pivot)
        cmds.move(toe_pos[0], toe_pos[1], toe_pos[2], toe_tip_pivot)

        cmds.parent(self.leg_ik, flex_pivot)
        cmds.parent(self.foot_ik, flex_pivot)
        cmds.parent(self.toe_ik, toe_tap_pivot)

        if not self.is_front:
            flex_offset = cmds.group(em=1, n='{}flex_offset'.format(self.base_name))
            cmds.move(foot_pos[0], foot_pos[1], foot_pos[2], flex_offset)

            cmds.parent(flex_pivot, flex_offset)
            cmds.parentConstraint(self.helpers[3], flex_offset, mo=1)
            cmds.parent(self.helper_ik, toe_tap_pivot)
            cmds.parent(toe_tap_pivot, toe_tip_pivot)
            cmds.parent(flex_offset, toe_tip_pivot)
            cmds.parent(toe_tip_pivot, swivel_pivot)
            cmds.parent(swivel_pivot, self.ctrls[3])

            # pole vector setup
            cmds.poleVectorConstraint(self.ctrls[2], self.leg_ik)
            cmds.poleVectorConstraint(self.ctrls[2], self.helper_ik)
        else:
            wrist_pivot = cmds.group(em=1, n='{}wrist_pivot'.format(self.base_name))
            cmds.move(wrist_pos[0], wrist_pos[1], wrist_pos[2], wrist_pivot)

            hierarchy.batch_parent([toe_tap_pivot, flex_pivot], swivel_pivot)
            cmds.parent(swivel_pivot, toe_tip_pivot)
            cmds.parent(toe_tip_pivot, wrist_pivot)
            cmds.parent(wrist_pivot, self.ctrls[3])

            cmds.connectAttr(self.ctrls[3]+'.wr', wrist_pivot+'.rx')

            # pole vector setup
            cmds.poleVectorConstraint(self.ctrls[1], self.leg_ik)

        cmds.connectAttr(self.ctrls[3]+'.flx', flex_pivot+'.rx')
        cmds.connectAttr(self.ctrls[3]+'.swv', swivel_pivot+'.ry')
        cmds.connectAttr(self.ctrls[3]+'.tap', toe_tap_pivot+'.rx')
        cmds.connectAttr(self.ctrls[3]+'.tip', toe_tip_pivot+'.rx')

        # Scalable rig setup
        self.add_measurement()
