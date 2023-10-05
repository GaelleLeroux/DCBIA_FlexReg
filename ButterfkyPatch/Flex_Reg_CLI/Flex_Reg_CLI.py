#!/usr/bin/env python-real

import argparse
import vtk
from Method.make_butterfly import butterflyPatch
from Method.draw import drawPatch
import os 
import numpy as np


def main(args):
    os.makedirs("/home/luciacev/Documents/Gaelle/Data/Flex_Reg/bonjour",exist_ok=True)
    print("dans cli avant traitement")
    print(args.lineedit)
    reader = vtk.vtkPolyDataReader()
    reader.SetFileName(args.lineedit)
    reader.Update()
    modelNode = reader.GetOutput()
    print("_"*150)
    print("type modelNode cli : ",type(modelNode))

    if args.type=="butterfly":
    # modelNode = vtk.vtkPolyDataReader(args.lineedit)
        butterflyPatch(modelNode,
                        args.lineedit_teeth_left_top,
                        args.lineedit_teeth_right_top,
                        args.lineedit_teeth_left_bot,
                        args.lineedit_teeth_right_bot,
                        args.lineedit_ratio_left_top,
                        args.lineedit_ratio_right_top,
                        args.lineedit_ratio_left_bot,
                        args.lineedit_ratio_right_bot,
                        args.lineedit_adjust_left_top,
                        args.lineedit_adjust_right_top,
                        args.lineedit_adjust_left_bot,
                        args.lineedit_adjust_right_bot)
    
    elif args.type=="curve":
        x, y, z = map(float, args.middle_point.split(','))
        middle = vtk.vtkVector3d(x, y, z)

        print("middle : ",middle)
        print("type middle",type(middle))

        # Splitting the string into individual array-like strings
        array_strings = args.curve.split('],[')

        # Initializing an empty list to store the ndarrays
        arrays = []

        # Looping through each array-like string to convert them into numpy arrays
        for array_string in array_strings:
            # Removing the brackets and splitting by spaces to get individual numbers
            numbers = array_string.replace('[', '').replace(']', '').split()
            # Converting the numbers into a numpy array and appending to the list
            arrays.append(np.array([float(num) for num in numbers]))

        curve =[arr.astype(np.float32) for arr in arrays]
        print("curve : ",curve)
        print("type curve : ",type(curve))
        print("type element curve : ",type(curve[0]))

        drawPatch(curve,modelNode,middle)
        print("noo"*150)


    modelNode.Modified()
    writer = vtk.vtkPolyDataWriter()
    writer.SetFileName(args.lineedit)
    writer.SetInputData(modelNode)
    writer.Write()

    print("dans cli apres traitement")

    







if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('lineedit',type=str)

    parser.add_argument('lineedit_teeth_left_top',type=int)
    parser.add_argument('lineedit_teeth_right_top',type=int)
    parser.add_argument('lineedit_teeth_left_bot',type=int)
    parser.add_argument('lineedit_teeth_right_bot',type=int)

    parser.add_argument('lineedit_ratio_left_top',type=float)
    parser.add_argument('lineedit_ratio_right_top',type=float)
    parser.add_argument('lineedit_ratio_left_bot',type=float)
    parser.add_argument('lineedit_ratio_right_bot',type=float)

    parser.add_argument('lineedit_adjust_left_top',type=float)
    parser.add_argument('lineedit_adjust_right_top',type=float)
    parser.add_argument('lineedit_adjust_left_bot',type=float)
    parser.add_argument('lineedit_adjust_right_bot',type=float)

    parser.add_argument('curve',type=str)
    parser.add_argument('middle_point',type=str)
    parser.add_argument('type',type=str)
    
    


    args = parser.parse_args()


    main(args)