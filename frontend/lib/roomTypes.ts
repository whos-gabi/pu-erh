export function isSeatId(id: string): boolean {
  return /^scaun/i.test(id);
}

export function isMeetingRoomId(id: string): boolean {
  return /^meetingRoom\d+/i.test(id);
}

export function isMeetingLargeId(id: string): boolean {
  return /^meetingLarge\d+/i.test(id);
}

export function isMeetingStationId(id: string): boolean {
  return /^meetingStation\d*/i.test(id);
}

export function isMeetingBoothId(id: string): boolean {
  return /^meetingBooth\d*/i.test(id);
}

export function isBeerPointArea(id: string): boolean {
  return /^beerPointArea/i.test(id);
}

export function isMassageArea(id: string): boolean {
  return /^massageArea/i.test(id);
}

export function requiresApproval(id: string): boolean {
  // Require approval for: meetingLarge1/2+, beerPointArea*, meetingRoom1-4
  if (isMeetingLargeId(id)) return true;
  if (isBeerPointArea(id)) return true;
  if (isMeetingRoomId(id)) {
    const m = id.match(/meetingRoom(\d+)/i);
    const num = m ? parseInt(m[1], 10) : NaN;
    if (!Number.isNaN(num) && num >= 1 && num <= 4) {
      return true;
    }
  }
  return false;
}


