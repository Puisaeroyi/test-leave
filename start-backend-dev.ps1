Start-Process `
  -FilePath powershell `
  -ArgumentList '-NoExit', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', 'D:\sol\test-leave\run-backend-dev.ps1' `
  -WindowStyle Normal
