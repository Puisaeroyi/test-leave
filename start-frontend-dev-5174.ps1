Start-Process `
  -FilePath powershell `
  -ArgumentList '-NoExit', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', 'D:\sol\test-leave\run-frontend-dev-5174.ps1' `
  -WindowStyle Normal
