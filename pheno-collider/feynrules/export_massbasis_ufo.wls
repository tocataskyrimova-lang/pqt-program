(*
 * Wolfram Script to Export PQT Memory Sector Mass Basis UFO
 * Usage: wolframscript -file export_massbasis_ufo.wls <FEYNRULES_PATH> <MODEL_DIR> <OUTPUT_DIR>
 *)

If[Length[$ScriptCommandLine] < 4,
  Print["Usage: wolframscript -file export_massbasis_ufo.wls <FEYNRULES_PATH> <MODEL_DIR> <OUTPUT_DIR>"];
  Exit[1];
];

feynrulesPath = $ScriptCommandLine[[2]];
modelDir = $ScriptCommandLine[[3]];
outputDir = $ScriptCommandLine[[4]];

Print["FeynRules Path: ", feynrulesPath];
Print["Model Directory: ", modelDir];
Print["Output Directory: ", outputDir];

(* Add FeynRules to path *)
If[!MemberQ[$Path, feynrulesPath], AppendTo[$Path, feynrulesPath]];

(* Load FeynRules *)
Print["Loading FeynRules..."];
<< FeynRules`;
Print["FeynRules loaded successfully."];

(* Load SM model *)
smPath = FileNameJoin[{feynrulesPath, "Models", "SM", "SM.fr"}];
If[!FileExistsQ[smPath],
  Print["Error: SM.fr not found at ", smPath];
  Exit[1];
];
Print["Loading SM model from ", smPath];
LoadModel[smPath];
Print["SM model loaded."];

(* Load PQT mass basis model *)
modelPath = FileNameJoin[{modelDir, "PQT_MemorySector_massbasis.fr"}];
If[!FileExistsQ[modelPath],
  Print["Error: PQT_MemorySector_massbasis.fr not found at ", modelPath];
  Exit[1];
];
Print["Loading PQT Memory Sector Mass Basis model from ", modelPath];
LoadModel[modelPath];
Print["PQT model loaded successfully."];

(* Build Feynman rules *)
Print["Building Feynman rules..."];
BuildFeynmanRules[];
Print["Feynman rules built."];

(* Export UFO *)
Print["Exporting UFO to ", outputDir];
If[!DirectoryQ[outputDir], CreateDirectory[outputDir]];
ExportUFO[outputDir];
Print["UFO exported successfully to ", outputDir];

Exit[0];
