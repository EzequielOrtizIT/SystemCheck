# Forzamos UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# --- 1. SISTEMA OPERATIVO ---
$osInfo = Get-CimInstance Win32_OperatingSystem
$sysDrive = $osInfo.SystemDrive 
$sysLetter = $sysDrive.Replace(":", "")
$osStr = "$($osInfo.Caption) - Ver: $($osInfo.Version) (Instalado en $sysDrive)"

# --- 2. PLACA BASE ---
$mobo = Get-CimInstance Win32_BaseBoard
$moboStr = "$($mobo.Manufacturer) - $($mobo.Product)"

# --- 3. PROCESADOR ---
$cpu = Get-CimInstance Win32_Processor
$cpuStr = $cpu.Name

# --- 4. MEMORIA RAM ---
$ramSticks = Get-CimInstance Win32_PhysicalMemory
$ramDetails = @()
$totalRam = 0
foreach ($stick in $ramSticks) {
    $gb = $stick.Capacity / 1GB
    $totalRam += $gb
    $ramDetails += "$([math]::Round($gb))GB @ $($stick.Speed)MHz"
}
$ramTextSticks = $ramDetails -join " | "
$ramStr = "$totalRam GB Total [ $ramTextSticks ]"

# --- 5. VIDEO (Con Fix 64bits) ---
$gpus = Get-CimInstance Win32_VideoController
$gpuList = @()
$regBase = "HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
foreach ($gpu in $gpus) {
    $vramGB = 0
    if ($gpu.AdapterRAM -gt 0) { $vramGB = $gpu.AdapterRAM / 1GB }
    if ($vramGB -le 4) {
        try {
            $driverKeys = Get-ChildItem $regBase -ErrorAction SilentlyContinue
            foreach ($key in $driverKeys) {
                $props = Get-ItemProperty $key.PSPath -ErrorAction SilentlyContinue
                if ($props.DriverDesc -eq $gpu.Name -or $props.DriverDesc -eq $gpu.Caption) {
                    if ($null -ne $props."HardwareInformation.qwMemorySize") {
                        $vramGB = $props."HardwareInformation.qwMemorySize" / 1GB
                        break
                    }
                }
            }
        } catch {}
    }
    $vramFinal = [math]::Round($vramGB, 0)
    $gpuList += "$($gpu.Name) ($vramFinal GB)"
}
$vgaStr = $gpuList -join " | "

# --- 6. ALMACENAMIENTO ---
$diskDetails = @()
$disks = Get-PhysicalDisk | Where-Object { $_.MediaType -ne 'Unspecified' } | Sort-Object Number
foreach ($disk in $disks) {
    try { $diskNumber = ($disk | Get-Disk).Number } catch { $diskNumber = $disk.DeviceId }
    $infoDisco = "💿 DISCO #$diskNumber : $($disk.FriendlyName) ($($disk.MediaType))"
    if ($null -ne $diskNumber) {
        try { $partitions = Get-Partition -DiskNumber $diskNumber -ErrorAction Stop | Where-Object { $_.DriveLetter } } catch { $partitions = $null }
    }
    if ($partitions) {
        foreach ($part in $partitions) {
            $vol = Get-Volume -DriveLetter $part.DriveLetter
            if ($vol.Size -gt 0) {
                $freeGB = [math]::Round($vol.SizeRemaining / 1GB, 2)
                $totalGB = [math]::Round($vol.Size / 1GB, 2)
                $percent = [math]::Round(($vol.SizeRemaining / $vol.Size) * 100, 1)
                $marca = ""; if ($part.DriveLetter -eq $sysLetter) { $marca = " ⭐ (SISTEMA)" }
                $infoDisco += "`n   └── [$($part.DriveLetter):] Libre: $freeGB / $totalGB GB ($percent%)$marca"
            }
        }
    }
    $diskDetails += $infoDisco
    $diskDetails += "----------------------------------"
}
$diskFinalText = $diskDetails -join "`n"

# --- 7. RED AVANZADA (NUEVO) ---
$netConfig = Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -ne $null -and $_.NetAdapter.Status -eq "Up" } | Select-Object -First 1

if ($netConfig) {
    $netAdapter = Get-NetAdapter -InterfaceIndex $netConfig.InterfaceIndex
    $adapterName = $netAdapter.InterfaceDescription
    $macAddress = $netAdapter.MacAddress
    
    # Velocidad formateada
    $speedRaw = $netAdapter.LinkSpeed
    if ($speedRaw -like "*Gbps*") { $speedStr = "$speedRaw (Gigabit 🚀)" } 
    elseif ($speedRaw -like "*100 Mbps*") { $speedStr = "$speedRaw (⚠️ Lento)" } 
    else { $speedStr = $speedRaw }

    $ipAddress = $netConfig.IPv4Address.IPAddress
    $gateway = $netConfig.IPv4DefaultGateway.NextHop
    $dnsServers = $netConfig.DNSServer.ServerAddresses -join ", "

    # Ping
    if (Test-Connection -ComputerName 8.8.8.8 -Count 1 -Quiet -ErrorAction SilentlyContinue) { 
        $pingStr = "✅ Conectado a Internet" 
    } else { 
        $pingStr = "❌ Sin Internet" 
    }
} else {
    $adapterName = "Sin red activa"; $macAddress = "-"; $speedStr = "-"
    $ipAddress = "-"; $gateway = "-"; $dnsServers = "-"; $pingStr = "❌ Desconectado"
}

# --- JSON FINAL ---
$PCData = @{
    cpu=$cpuStr; mobo=$moboStr; ram=$ramStr; vga=$vgaStr; os=$osStr; disk=$diskFinalText
    net_name=$adapterName; net_mac=$macAddress; net_speed=$speedStr
    net_ip=$ipAddress; net_gw=$gateway; net_dns=$dnsServers; net_ping=$pingStr
}
$PCData | ConvertTo-Json -Compress