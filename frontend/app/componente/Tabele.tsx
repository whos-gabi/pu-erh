"use client";
import React, { useState } from "react";

type CartItem = {
  class: string;
  model_id: string;
  item_id: string;
  pret: number;
  quantity: number;
};

type RowData = {
  id: number;
  created_at: string;
  name: string;
  email: string;
  telefon: string;
  status: string;
  cart: CartItem[];
};

type Props = {
  dat: any;
};

export default function Tabele({ dat }: Props) {
  const [modalCart, setModalCart] = useState<CartItem[] | null>(null);
  const [data, setData] = useState<RowData[]>(dat);
  console.log(dat);

  const closeModal = () => setModalCart(null);

  async function handleStatusChange(id: number, newStatus: string) {
    // const res = await supabase
    //   .from("Orders")
    //   .update({ status: newStatus })
    //   .eq("id", id);
    // console.log(res);
    // if (res.status == 204)
    //   setData((prevData: any) =>
    //     prevData.map((row: any) =>
    //       row.id === id ? { ...row, status: newStatus } : row
    //     )
    //   );
  }

  return (
    <div className="">
      <div className="overflow-x-auto bg-gray-100 rounded-lg shadow-md">
        <table className="w-full text-sm text-left text-gray-600">
          <thead className="bg-gray-200 text-gray-800">
            <tr>
              {["ID", "Data", "Name & Email", "Telefon", "Status", "Cart"].map(
                (column, index) => (
                  <th
                    key={index}
                    className="px-4 py-3 text-sm font-semibold uppercase tracking-wider"
                  >
                    {column}
                  </th>
                )
              )}
            </tr>
          </thead>
          <tbody>
            {data
              .slice()
              .reverse()
              .map((row, index) => (
                <tr
                  key={row.id}
                  className={`${
                    index % 2 === 0 ? "bg-gray-50" : "bg-white"
                  } hover:bg-gray-100 transition duration-150 ease-in-out`}
                >
                  <td className="px-4 py-3">{row.id}</td>
                  <td className="px-4 py-3">
                    {(() => {
                      const date = new Date(row.created_at);
                      const formattedDate = date.toLocaleString("en-US", {
                        weekday: "long", // Full weekday (e.g., Monday)
                        year: "numeric", // Full year (e.g., 2024)
                        month: "long", // Full month (e.g., December)
                        day: "numeric", // Numeric day of the month (e.g., 30)
                      });
                      const formattedTime = date.toLocaleString("en-US", {
                        hour: "numeric", // Hour (e.g., 2)
                        minute: "numeric", // Minute (e.g., 30)
                        second: "numeric", // Second (e.g., 03)
                        hour12: true, // 12-hour clock
                      });

                      return (
                        <>
                          <div>{formattedDate}</div>
                          <div>{formattedTime}</div>
                        </>
                      );
                    })()}
                  </td>
                  <td className="px-4 py-3">
                    <div>
                      <p className="font-medium">{row.name}</p>
                      <p className="text-xs text-gray-500">{row.email}</p>
                    </div>
                  </td>
                  <td className="px-4 py-3">{row.telefon}</td>
                  <td className="px-4 py-3">
                    <select
                      value={row.status}
                      onChange={(e) =>
                        handleStatusChange(row.id, e.target.value)
                      }
                      className={`px-2 py-1 rounded-full text-xs font-medium appearance-none flex justify-center ${
                        row.status === "done"
                          ? "bg-green-200 text-green-800"
                          : row.status === "pending"
                          ? "bg-yellow-200 text-yellow-800"
                          : "bg-red-200 text-red-800"
                      }`}
                    >
                      <option value="done">Done</option>
                      <option value="declined">Declined</option>
                      <option value="pending">Pending</option>
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    <a
                      onClick={() => setModalCart(row.cart)}
                      className="px-2 cursor-pointer hover:underline"
                    >
                      {`[...]`}
                    </a>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {modalCart && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-lg font-bold mb-4">Cart Details</h2>
            <table className="w-full text-sm text-left text-gray-600">
              <thead className="bg-gray-200 text-gray-800">
                <tr>
                  {[
                    "Categorie",
                    "Model ID",
                    "Item ID",
                    "Pret",
                    "Cantitate",
                    "Pret Item ",
                  ].map((header, index) => (
                    <th
                      key={index}
                      className="px-4 py-3 text-sm font-semibold uppercase tracking-wider"
                    >
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {modalCart.map((item) => (
                  <tr key={item.item_id} className="hover:bg-gray-100">
                    <td className="px-4 py-3">
                      {item.class[0].toUpperCase() + item.class.slice(1)}
                    </td>
                    <td className="px-4 py-3">{item.model_id}</td>
                    <td className="px-4 py-3">{item.item_id}</td>
                    <td className="px-4 py-3">{item.pret}</td>
                    <td className="px-4 py-3">{item.quantity}</td>
                    <td className="px-4 py-3">{item.quantity * item.pret}</td>
                  </tr>
                ))}
                <tr className="font-bold hover:bg-gray-100">
                  <td colSpan={5} className="px-4 py-3 text-right">
                    Pret total
                  </td>
                  <td className="px-4 py-3">
                    {modalCart.reduce(
                      (acc, item) => acc + item.pret * item.quantity,
                      0
                    )}
                  </td>
                </tr>
              </tbody>
            </table>
            <button
              onClick={closeModal}
              className="mt-4 px-4 py-2 text-sm font-medium text-white bg-red-600 rounded hover:bg-red-700"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
