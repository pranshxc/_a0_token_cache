export default async function registerTokenMeterSurface(surfaces) {
  surfaces.push({
    id:    "token-meter",
    icon:  "monitoring",
    label: "Token Meter",
    component: "token-meter-panel",
  });
}
