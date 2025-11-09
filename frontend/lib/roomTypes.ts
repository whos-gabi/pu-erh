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
  // Require approval for:
  // - meetingLarge{n} and meetingLargeArea{n}
  // - beerPointArea*
  // - meetingRoom{1-6} and meetingRoomArea{1-6}
  if (isBeerPointArea(id)) return true;
  // Match both base and Area variants
  const large = id.match(/meetingLarge(?:Area)?(\d+)/i);
  if (large) return true;
  const room = id.match(/meetingRoom(?:Area)?(\d+)/i);
  if (room) {
    const num = parseInt(room[1], 10);
    if (!Number.isNaN(num) && num >= 1 && num <= 6) return true;
  }
  return false;
}


