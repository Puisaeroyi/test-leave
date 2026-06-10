export function calculateHourRange(startHour, endHour) {
  if (startHour == null || endHour == null || startHour === endHour) return 0;
  return endHour > startHour ? endHour - startHour : 24 - startHour + endHour;
}

export function getCustomHourOffsets(startHour, endHour, startDayOffset = 0) {
  return {
    startDayOffset,
    endDayOffset: endHour <= startHour ? startDayOffset + 1 : startDayOffset,
  };
}

function timeToMinutes(value) {
  const [hours, minutes = 0] = String(value).split(":").map(Number);
  return hours * 60 + minutes;
}

export function inferCustomHourOffsets(startHour, endHour, shift) {
  if (!shift) return getCustomHourOffsets(startHour, endHour, 0);

  const startMinutes = startHour * 60;
  const endMinutes = endHour * 60;
  const shiftStart = timeToMinutes(shift.start_time);
  const shiftEnd = timeToMinutes(shift.end_time);
  if (shiftEnd > shiftStart) return getCustomHourOffsets(startHour, endHour, 0);

  const startDayOffset = startMinutes < shiftStart ? 1 : 0;
  let endDayOffset = endMinutes <= shiftEnd ? 1 : 0;
  if (endMinutes <= startMinutes && endDayOffset <= startDayOffset) {
    endDayOffset = startDayOffset + 1;
  }
  return { startDayOffset, endDayOffset };
}
