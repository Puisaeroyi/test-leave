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

export function inferCustomHourOffsets(startHour, endHour) {
  return getCustomHourOffsets(startHour, endHour, 0);
}
