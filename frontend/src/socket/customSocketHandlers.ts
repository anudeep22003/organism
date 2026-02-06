export const dummyPrint = () => {
  console.log(
    "dummy print from dummyPrint function that was triggered by a socket event, yayyy"
  );
};

export const customHandlers = {
  dummy: () => {
    dummyPrint();
  },
};
