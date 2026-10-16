$outputDir = "D:\5ds\deep\output\test-claim"
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
$voice = New-Object -ComObject SAPI.SpVoice
$stream = New-Object -ComObject SAPI.SpFileStream
$audioPath = Join-Path $outputDir "07_declaration_audio.wav"
$stream.Open($audioPath, 3, $false)
$voice.AudioOutputStream = $stream
$text = "Bonjour, je m'appelle Inès Ben Salem. Je déclare un accident survenu le douze octobre deux mille vingt-six, vers dix-sept heures quarante, avenue Habib Bourguiba à Tunis. Je ralentissais devant un passage piéton lorsqu'une voiture m'a percutée à l'arrière. Le choc a endommagé le pare-chocs arrière gauche et légèrement fissuré le feu arrière gauche de ma Renault Clio blanche. Il n'y a aucun blessé et la voiture reste roulante. Mon numéro de contrat est AUTO T N deux mille vingt-six zéro zéro quarante-deux."
$voice.Speak($text) | Out-Null
$stream.Close()
Write-Output $audioPath
