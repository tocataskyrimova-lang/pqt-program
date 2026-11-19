frPath   = $ScriptCommandLine[[2]];
modelDir = $ScriptCommandLine[[3]];
outDir   = $ScriptCommandLine[[4]];

Print["FeynRules path: ", frPath];
Print["Model dir: ", modelDir];
Print["Output dir: ", outDir];

$FeynRulesPath = frPath;
FR$Parallel = False;
Get[FileNameJoin[{frPath, "FeynRules.m"}]];

sm = FileNameJoin[{frPath, "Models", "SM", "SM.fr"}];
model = FileNameJoin[{modelDir, "PQT_MemorySector_massbasis_SMext.fr"}];

If[!FileExistsQ[sm], Print["ERROR: SM.fr not found: ", sm]; Exit[1];];
If[!FileExistsQ[model], Print["ERROR: PQT model not found: ", model]; Exit[1];];

Print["Loading SM.fr + PQT extension..."];
LoadModel[sm, model];

Print["ValueQ[LSM] = ", ValueQ[LSM]];
Print["ValueQ[LPQTMassBasis] = ", ValueQ[LPQTMassBasis]];

If[!ValueQ[LSM],
  txt = Import[sm, "Text"];
  Print["ERROR: LSM is not defined after loading SM.fr"];
  Print["SM lagrangian candidates: ", StringCases[txt, Shortest[("LSM" | "LTotal" | "Lag" | "Lagrangian") ~~ ":=" ~~ __]]];
  Exit[1];
];

If[!ValueQ[LPQTMassBasis],
  Print["ERROR: LPQTMassBasis is not defined after loading PQT extension"];
  Exit[1];
];

auditText = Import[sm, "Text"];
requiredPatterns = {"Z[mu]", "W[mu]", "Wbar[mu]", "MW", "MZ", "vev"};
Print["SM symbol audit:"];
Do[
  Print["  ", pat, " -> ", StringContainsQ[auditText, pat]],
  {pat, requiredPatterns}
];

LExport = LSM + LPQTMassBasis;

If[DirectoryQ[outDir], DeleteDirectory[outDir, DeleteContents -> True]];
CreateDirectory[outDir, CreateIntermediateDirectories -> True];

Print["Writing UFO..."];
WriteUFO[LExport, Output -> outDir, AddDecays -> False, FlavorExpand -> False];

Print["UFO export complete."];
Exit[0];
