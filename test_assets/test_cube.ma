//Maya ASCII 2023 scene
//Name: test_cube.ma
//Last modified: Mon, Jul 28, 2025 07:02:52 pm
//Codeset: UTF-8
requires maya "2023";
requires "mtoa" "5.2.1.1";
requires -dataType "pxrUsdStageData" "mayaUsdPlugin" "0.20.0";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2023";
fileInfo "version" "2023";
fileInfo "cutIdentifier" "202211021031-847a9f9623";
fileInfo "osv" "Linux 4.18.0-553.8.1.el8_10.x86_64 #1 SMP Fri Jun 14 03:19:37 EDT 2024 x86_64";
fileInfo "UUID" "1D6B11C0-0009-2A09-6887-BB4C00000411";
fileInfo "license" "education";
createNode transform -n "pCube1";
	rename -uid "1D6B11C0-0009-2A09-6887-BB20000003FD";
	setAttr ".t" -type "double3" -10.602133638826992 0 8.4741256554363318 ;
	setAttr ".s" -type "double3" 3.0622878698429097 3.0622878698429097 3.0622878698429097 ;
createNode mesh -n "pCubeShape1" -p "pCube1";
	rename -uid "1D6B11C0-0009-2A09-6887-BB20000003FC";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
createNode polyCube -n "polyCube1";
	rename -uid "1D6B11C0-0009-2A09-6887-BB20000003FB";
	setAttr ".cuv" 4;
select -ne :time1;
	setAttr ".o" 0;
select -ne :hardwareRenderingGlobals;
	setAttr ".otfna" -type "stringArray" 22 "NURBS Curves" "NURBS Surfaces" "Polygons" "Subdiv Surface" "Particles" "Particle Instance" "Fluids" "Strokes" "Image Planes" "UI" "Lights" "Cameras" "Locators" "Joints" "IK Handles" "Deformers" "Motion Trails" "Components" "Hair Systems" "Follicles" "Misc. UI" "Ornaments"  ;
	setAttr ".otfva" -type "Int32Array" 22 0 1 1 1 1 1
		 1 1 1 0 0 0 0 0 0 0 0 0
		 0 0 0 0 ;
	setAttr ".fprt" yes;
select -ne :renderPartition;
	setAttr -s 4 ".st";
select -ne :renderGlobalsList1;
select -ne :defaultShaderList1;
	setAttr -s 7 ".s";
select -ne :postProcessList1;
	setAttr -s 2 ".p";
select -ne :defaultRenderingList1;
select -ne :initialShadingGroup;
	setAttr -s 4 ".dsm";
	setAttr ".ro" yes;
select -ne :initialParticleSE;
	setAttr ".ro" yes;
select -ne :defaultRenderGlobals;
	setAttr ".ren" -type "string" "arnold";
select -ne :defaultResolution;
	setAttr ".pa" 1;
select -ne :defaultColorMgtGlobals;
	setAttr ".cfe" yes;
	setAttr ".cfp" -type "string" "<MAYA_RESOURCES>/OCIO-configs/Maya2022-default/config.ocio";
	setAttr ".vtn" -type "string" "ACES 1.0 SDR-video (sRGB)";
	setAttr ".vn" -type "string" "ACES 1.0 SDR-video";
	setAttr ".dn" -type "string" "sRGB";
	setAttr ".wsn" -type "string" "ACEScg";
	setAttr ".otn" -type "string" "ACES 1.0 SDR-video (sRGB)";
	setAttr ".potn" -type "string" "ACES 1.0 SDR-video (sRGB)";
select -ne :hardwareRenderGlobals;
	setAttr ".ctrs" 256;
	setAttr ".btrs" 512;
connectAttr "polyCube1.out" "pCubeShape1.i";
connectAttr "pCubeShape1.iog" ":initialShadingGroup.dsm" -na;
// End of test_cube.ma
