function normalizeText(value) {
  return String(value === undefined || value === null ? '' : value).trim()
}

function parseIpParts(ip) {
  const text = normalizeText(ip)
  const parts = text.split('.')

  if (parts.length !== 4) {
    return null
  }

  const nums = parts.map(function (part) {
    if (!/^\d+$/.test(part)) {
      return NaN
    }

    return Number(part)
  })

  if (nums.some(function (num) {
    return !Number.isInteger(num) || num < 0 || num > 255
  })) {
    return null
  }

  return nums
}

function isValidIp(ip) {
  return !!parseIpParts(ip)
}

function ipToInt(ip) {
  const parts = parseIpParts(ip)

  if (!parts) {
    throw new Error('请输入合法 IPv4 地址。')
  }

  return (((parts[0] << 24) >>> 0) +
    ((parts[1] << 16) >>> 0) +
    ((parts[2] << 8) >>> 0) +
    parts[3]) >>> 0
}

function intToIp(num) {
  const value = Number(num) >>> 0

  return [
    (value >>> 24) & 255,
    (value >>> 16) & 255,
    (value >>> 8) & 255,
    value & 255
  ].join('.')
}

function parseCidr(cidr) {
  const text = normalizeText(cidr)

  if (!/^\d+$/.test(text)) {
    return NaN
  }

  return Number(text)
}

function isValidCidr(cidr) {
  const value = parseCidr(cidr)

  return Number.isInteger(value) && value >= 0 && value <= 32
}

function assertCidr(cidr) {
  const value = parseCidr(cidr)

  if (!Number.isInteger(value) || value < 0 || value > 32) {
    throw new Error('掩码位必须是 0 - 32 的整数。')
  }

  return value
}

function cidrToMask(cidr) {
  const value = assertCidr(cidr)
  const maskInt = value === 0 ? 0 : (0xffffffff << (32 - value)) >>> 0

  return intToIp(maskInt)
}

function maskToCidr(mask) {
  if (!isValidIp(mask)) {
    throw new Error('请输入合法且连续的子网掩码。')
  }

  const maskInt = ipToInt(mask)
  const binary = toBinary32(maskInt)

  if (!/^1*0*$/.test(binary)) {
    throw new Error('请输入合法且连续的子网掩码。')
  }

  const cidr = binary.indexOf('0') === -1 ? 32 : binary.indexOf('0')

  if (cidrToMask(cidr) !== normalizeText(mask)) {
    throw new Error('请输入合法且连续的子网掩码。')
  }

  return cidr
}

function cidrToWildcard(cidr) {
  const value = assertCidr(cidr)
  const maskInt = ipToInt(cidrToMask(value))

  return intToIp((~maskInt) >>> 0)
}

function maskToWildcard(mask) {
  const cidr = maskToCidr(mask)

  return cidrToWildcard(cidr)
}

function toBinary8(num) {
  return (num >>> 0).toString(2).padStart(8, '0')
}

function toBinary32(num) {
  const value = Number(num) >>> 0

  return toBinary8((value >>> 24) & 255) +
    toBinary8((value >>> 16) & 255) +
    toBinary8((value >>> 8) & 255) +
    toBinary8(value & 255)
}

function ipToBinary(ip) {
  const parts = parseIpParts(ip)

  if (!parts) {
    throw new Error('请输入合法 IPv4 地址。')
  }

  return parts.map(toBinary8).join('.')
}

function maskToHex(mask) {
  maskToCidr(mask)

  return parseIpParts(mask).map(function (part) {
    return Number(part).toString(16).toUpperCase().padStart(2, '0')
  }).join('.')
}

function calculateNetwork(ip, cidr) {
  if (!normalizeText(ip)) {
    throw new Error('IP 地址不能为空。')
  }

  if (!isValidIp(ip)) {
    throw new Error('请输入合法 IPv4 地址。')
  }

  const cidrValue = assertCidr(cidr)
  const ipInt = ipToInt(ip)
  const mask = cidrToMask(cidrValue)
  const maskInt = ipToInt(mask)
  const wildcardInt = (~maskInt) >>> 0
  const networkInt = (ipInt & maskInt) >>> 0
  const broadcastInt = (networkInt | wildcardInt) >>> 0
  const totalCount = Math.pow(2, 32 - cidrValue)
  let usableCount = totalCount
  let firstUsableInt = networkInt
  let lastUsableInt = broadcastInt
  let note = ''

  if (cidrValue <= 30) {
    usableCount = totalCount - 2
    firstUsableInt = (networkInt + 1) >>> 0
    lastUsableInt = (broadcastInt - 1) >>> 0
  }

  if (cidrValue === 31) {
    note = '/31 常用于点到点链路'
  }

  if (cidrValue === 32) {
    note = '/32 为单主机地址'
  }

  return {
    cidr: normalizeText(ip) + '/' + cidrValue,
    cidrValue: cidrValue,
    subnetMask: mask,
    wildcardMask: intToIp(wildcardInt),
    networkAddress: intToIp(networkInt),
    broadcastAddress: intToIp(broadcastInt),
    firstUsableAddress: intToIp(firstUsableInt),
    lastUsableAddress: intToIp(lastUsableInt),
    usableRange: intToIp(firstUsableInt) + ' - ' + intToIp(lastUsableInt),
    totalCount: totalCount,
    usableCount: usableCount,
    ipBinary: ipToBinary(ip),
    maskBinary: ipToBinary(mask),
    networkBinary: ipToBinary(intToIp(networkInt)),
    note: note
  }
}

function calculateRequiredCidr(hostCount) {
  const text = normalizeText(hostCount)

  if (!/^\d+$/.test(text) || Number(text) <= 0) {
    throw new Error('地址数量必须是正整数。')
  }

  const count = Number(text)

  if (count === 1) {
    return {
      mode: 'single',
      recommendedCidr: 32,
      recommendedMask: cidrToMask(32),
      totalCount: 1,
      usableCount: 1,
      description: '单主机地址场景可使用 /32'
    }
  }

  if (count === 2) {
    return {
      mode: 'dual',
      pointToPoint: {
        cidr: 31,
        mask: cidrToMask(31),
        totalCount: 2,
        usableCount: 2,
        description: '/31 常用于点到点链路'
      },
      normal: {
        cidr: 30,
        mask: cidrToMask(30),
        totalCount: 4,
        usableCount: 2,
        description: '普通局域网场景可使用 /30'
      }
    }
  }

  for (let hostBits = 2; hostBits <= 32; hostBits += 1) {
    const totalCount = Math.pow(2, hostBits)
    const usableCount = totalCount - 2

    if (usableCount >= count) {
      const cidr = 32 - hostBits

      return {
        mode: 'normal',
        recommendedCidr: cidr,
        recommendedMask: cidrToMask(cidr),
        totalCount: totalCount,
        usableCount: usableCount,
        description: '已选择能容纳该可用地址数量的最小子网'
      }
    }
  }

  throw new Error('地址数量超过 IPv4 可容纳范围。')
}

module.exports = {
  isValidIp,
  ipToInt,
  intToIp,
  isValidCidr,
  cidrToMask,
  maskToCidr,
  cidrToWildcard,
  maskToWildcard,
  ipToBinary,
  maskToHex,
  calculateNetwork,
  calculateRequiredCidr
}
