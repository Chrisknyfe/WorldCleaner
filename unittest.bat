' Test stuff!

GOTO:SMALLSURVIVAL

:NYLL

' Nyll, the spaceworld.
rmdir /s /q nyll-copy
xcopy /E /I nyll nyll-copy
worldcleaner.py -v -t SPACE nyll-copy

GOTO:EOF
:SKAIA

' Skaia, the sky land
rmdir /s /q skaia-copy
xcopy /E /I skaia skaia-copy
worldcleaner.py -v -c 8192 -t SKYLANDS skaia-copy

GOTO:EOF
:CREATIVE

' creative world
rmdir /s /q creative-copy
xcopy /E /I creative creative-copy
worldcleaner.py -v -c 8192 -t FLAT --flat-height 10 creative-copy

GOTO:EOF
:SMALLCREATIVE

' smaller creative world
rmdir /s /q smallcreative-copy
xcopy /E /I smallcreative smallcreative-copy
worldcleaner.py -v -c 8192 -t FLAT smallcreative-copy

GOTO:EOF
:NETHER

' the nether world
rmdir /s /q survival_nether-copy
xcopy /E /I survival_nether survival_nether-copy
worldcleaner.py -v -c 8192 -t NETHER survival_nether-copy

GOTO:EOF
:SURVIVAL

' Survival, but we're not ready for this yet.
rmdir /s /q survival-copy
xcopy /E /I Survival Survival-copy
worldcleaner.py -v -c 8192 -t NORMAL survival-copy

GOTO:EOF
:SMALLSURVIVAL

' Smaller Survival
rmdir /s /q smallsurvival-copy
xcopy /E /I smallsurvival smallsurvival-copy
worldcleaner.py -v -c 8192 -t NORMAL smallsurvival-copy
