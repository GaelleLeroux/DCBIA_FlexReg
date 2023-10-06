#!/usr/bin/env python-real

import argparse
import vtk
from Method.make_butterfly import butterflyPatch
from Method.draw import drawPatch
import os 
import numpy as np


def main(args):
    # os.makedirs("/home/luciacev/Documents/Gaelle/Data/Flex_Reg/bonjour",exist_ok=True)
    # Read the file (coordinate using : LPS)
    reader = vtk.vtkPolyDataReader()
    reader.SetFileName(args.lineedit)
    reader.Update()
    modelNode = reader.GetOutput()

    # Transform the data to read it in coordinate RAS (like slicer)
    transform = vtk.vtkTransform()
    transform.Scale(-1, -1, 1)

    transformFilter = vtk.vtkTransformPolyDataFilter()
    transformFilter.SetInputData(modelNode)
    transformFilter.SetTransform(transform)
    transformFilter.Update()

    modelNode = transformFilter.GetOutput()
   

    if args.type=="butterfly":
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
        # Reading the data
        vector_middle = args.middle_point[1:-1]
        x, y, z = map(float, vector_middle.split(','))
        middle = vtk.vtkVector3d(x, y, z)


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

        drawPatch(curve,modelNode,middle)
        print("noo"*150)

    # Save the changement in modelNode
    modelNode.Modified()

    # Put back the data in the LPS coordinate
    inverseTransform = vtk.vtkTransform()
    inverseTransform.Scale(-1, -1, 1)

    inverseTransformFilter = vtk.vtkTransformPolyDataFilter()
    inverseTransformFilter.SetInputData(modelNode)
    inverseTransformFilter.SetTransform(inverseTransform)
    inverseTransformFilter.Update()

    modelNode = inverseTransformFilter.GetOutput()

    modelNode.Modified()

    # Save the new file with the model
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