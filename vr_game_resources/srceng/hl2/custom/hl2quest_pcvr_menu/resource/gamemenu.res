"GameMenu"
{
	"1"
	{
		"label" "#GameUI_GameMenu_ResumeGame"
		"command" "ResumeGame"
		"InGameOrder" "10"
		"OnlyInGame" "1"
	}
	"2"
	{
		"label" "RECALIBRATE VIEW"
		"command" "engine hlvr_recalibrate_view"
		"InGameOrder" "18"
		"OnlyInGame" "1"
	}
	"3"
	{
		"label" "QUICK SAVE"
		"command" "engine save quick"
		"InGameOrder" "19"
		"OnlyInGame" "1"
	}
	"5"	
	{
		"label" "#GameUI_GameMenu_NewGame"
		"command" "OpenNewGameDialog"
		"InGameOrder" "40"
		"notmulti" "1"
	}
	"6"
	{
		"label" "#GameUI_GameMenu_LoadGame"
		"command" "OpenLoadGameDialog"
		"InGameOrder" "30"
		"notmulti" "1"
	}
	"7"
	{
		"label" "#GameUI_GameMenu_SaveGame"
		"command" "OpenSaveGameDialog"
		"InGameOrder" "20"
		"notmulti" "1"
		"OnlyInGame" "1"
	}
	"8"
	{
		"label" "#GameUI_GameMenu_Achievements"
		"command" "OpenAchievementsDialog"
		"InGameOrder" "50"
	}
	"10"
	{
		"label" "#GameUI_GameMenu_Options"
		"command" "engine ToggleVROptions"
		"InGameOrder" "70"
	}
	"11"
	{
		"label" "#hlvr_GameUI_Workshop"
		"command" "engine ToggleVRWorkshop"
		"InGameOrder" "80"
	}
	"12"
	{
		"label" "#GameUI_GameMenu_Quit"
		"command" "Quit"
		"InGameOrder" "90"
	}
}

