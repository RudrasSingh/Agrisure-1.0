truecolor_eval= """
//VERSION=3
let factor = 1/3000
return [factor*B04, factor*B03, factor*B02, dataMask]
"""


ndvi_eval = """
//VERSION=3
let ndvi = (B08 - B04) / (B08 + B04);

return colorBlend(ndvi,
   [-0.2, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0 ],
   [[0, 0, 0,dataMask],							   //  < -.2 = #000000 (black)
    [165/255,0,38/255,dataMask],        //  -> 0 = #a50026
    [215/255,48/255,39/255,dataMask],   //  -> .1 = #d73027
    [244/255,109/255,67/255,dataMask],  //  -> .2 = #f46d43
    [253/255,174/255,97/255,dataMask],  //  -> .3 = #fdae61
    [254/255,224/255,139/255,dataMask], //  -> .4 = #fee08b
    [255/255,255/255,191/255,dataMask], //  -> .5 = #ffffbf
    [217/255,239/255,139/255,dataMask], //  -> .6 = #d9ef8b
    [166/255,217/255,106/255,dataMask], //  -> .7 = #a6d96a
    [102/255,189/255,99/255,dataMask],  //  -> .8 = #66bd63
    [26/255,152/255,80/255,dataMask],   //  -> .9 = #1a9850
    [0,104/255,55/255,dataMask]         //  -> 1.0 = #006837
   ]);
"""

ndmi_eval = """//VERSION=3

if (B08 == 0 || B11 == 0){
  return [0,0,0];
} else {
  var val = (B08 - B11)/(B08 + B11);
  
  var vmin = -0.8;
  var vmax = 0.8;
  var dv = vmax - vmin;
  
  var r = 0.0;
  var g = 0.0;
  var b = 0.0;

  
  var v = val;

  if (v < vmin){
    v = vmin;
  }
  if (v > vmax){
    v = vmax;
  }
  
  var l1 = 0.35;
  var l2 = 0.48;
  var l3 = 0.52;
  var l4 = 0.65;
  
  var level1 = (vmin + l1 * dv);
  var level2 = (vmin + l2 * dv);
  var level3 = (vmin + l3 * dv);
  var level4 = (vmin + l4 * dv);

  if (v < level1){
     r = 0.5 +  (v - vmin) / (level1 - vmin) / 2;
  } else if (v < level2) {
     r = 1;
     g = (v - level1) / (level2 - level1);
     b = 0;
  } else if (v < level3) {
     r = 1 + (level2 - v) / (level3 - level2);
     g = 1;
     b = (v - level2) / (level3 - level2);
  } else if (v < level4) {
     r = 0;
     g = 1 + (level3 - v) / (level4 - level3);
     b = 1;
  } else {
     b = 1.0 + (level4 - v) / (vmax - level4) / 2;
  }

   return [r, g, b, dataMask];
}"""