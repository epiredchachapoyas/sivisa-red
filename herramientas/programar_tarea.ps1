# Crea (o actualiza) la tarea de Windows "SIVISA - publicar": cada 30 minutos y al iniciar sesion,
# ejecuta herramientas\actualizar.py sin abrir ventanas. Funciona tambien con la laptop a bateria.
param([Parameter(Mandatory=$true)][string]$Pythonw, [Parameter(Mandatory=$true)][string]$Raiz)
$script = Join-Path $Raiz "herramientas\actualizar.py"
$accion = New-ScheduledTaskAction -Execute $Pythonw -Argument ('"' + $script + '"') -WorkingDirectory $Raiz
$cada30 = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Days 3650)
$alEntrar = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$ajustes = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 20)
Register-ScheduledTask -TaskName "SIVISA - publicar" -Action $accion -Trigger @($cada30, $alEntrar) -Settings $ajustes -Description "Procesa las bases NotiSP y publica el portal SIVISA" -Force | Out-Null
Write-Host "Tarea 'SIVISA - publicar' programada (cada 30 minutos)."
