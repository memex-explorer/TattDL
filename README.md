# TattDL
Tattoo detection and localization

## Caffe Version
This uses the Caffe hash: 4115385deb3b907fcd428ac0ab53b694d741a3c4

## Getting the model
The tattoo model is managed by git-lfs, so make sure that is installed (see
`https://git-lfs.github.com/` for details on how to do that).

Then, fetch the file using:

  git lfs fetch
  git lfs checkout

## Detection output format
After running the `` tool, one of the output files will be a `detection.txt` file.
This is a CSV-like file (`|` primary separators):

  filename | proc time | scale | scores | boxes

The boxes field (the last one) may container 0 or more confidence and bounding box specifications.  Separating this text field by spaces (` `) will yield one or more sub-CSV rows with the format:

  confidence,x,y,width,height

X and Y coordinates specify the upper left corner of the sub-region, assuming (0,0) is the upper left corner of the image.

# Citation

Please cite the following paper if you use this software in your work:

```
@inproceedings{sun2016tattoo,
  title={Tattoo detection and localization using region-based deep learning},
  author={Sun, Zhaohui H and Baumes, Jeff and Tunison, Paul and Turek, Matt and Hoogs, Anthony},
  booktitle={Pattern Recognition (ICPR), 2016 23rd International Conference on},
  pages={3055--3060},
  year={2016},
  organization={IEEE}
}
```
Additionally, citing the JPL MEMEX project ```http://memex.jpl.nasa.gov/``` would be welcomed. 

