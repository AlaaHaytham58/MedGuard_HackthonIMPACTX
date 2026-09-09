// The medicine boxes offered on the Home picker. Photos are the team's own test
// images and every brand/ingredient pair is real — PRODUCT.md forbids fabricated
// packaging or brand names in any surface.
//
// `ingredient` is sent to the backend as `generic_name`, so it must be the plain
// ingredient the catalogue is keyed on: "Warfarin", never "Warfarin Sodium" —
// the salt suffix fails the lookup and the check silently returns nothing.
export const boxes = [
  {
    id: "panadol",
    brand: "Panadol Extra",
    ingredient: "Paracetamol",
    dosageMg: 500,
    image: "/images/panadol.jpg",
  },
  {
    id: "brufen",
    brand: "Brufen",
    ingredient: "Ibuprofen",
    dosageMg: 400,
    image: "/images/brufen.jpg",
  },
  {
    id: "concor",
    brand: "Concor",
    ingredient: "Bisoprolol",
    dosageMg: 5,
    image: "/images/concor.jpg",
  },
  {
    id: "marevan",
    brand: "Marevan",
    ingredient: "Warfarin",
    dosageMg: 5,
    image: "/images/marevan.jpg",
  },
];
