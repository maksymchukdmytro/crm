// pdfmake 0.2 (збірка для браузера) і шрифт Inter для нього (реєструється в window.pdfMake)
declare module "pdfmake/build/pdfmake" {
  const pdfMake: {
    createPdf: (def: unknown) => { getBlob: (cb: (b: Blob) => void) => void; open: () => void; download: (name?: string) => void };
    vfs?: Record<string, string>;
    fonts?: Record<string, unknown>;
  };
  export default pdfMake;
}
declare module "*inter-fonts.js";
