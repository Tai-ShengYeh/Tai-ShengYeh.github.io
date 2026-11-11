Add-Type -AssemblyName System.Speech
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$out = Join-Path $dir 'narration.wav'
$textPath = Join-Path $dir 'narration.txt'
$text = Get-Content -LiteralPath $textPath -Raw -Encoding UTF8
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice('Microsoft Hanhan Desktop')
$s.Rate = -1
$s.Volume = 100
$s.SetOutputToWaveFile($out)
$s.Speak($text)
$s.Dispose()
Write-Output $out
