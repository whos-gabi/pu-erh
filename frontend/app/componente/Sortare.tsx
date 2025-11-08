"use client";
import { useEffect, useRef, useState } from "react";
import { ChevronDown, Filter, LayoutGrid } from "lucide-react";
import Link from "next/link";

type Types = {
  totalCount: number;
  tabel: string;
  id: string;
  selectedSort: string;
  setSelectedSort: React.Dispatch<React.SetStateAction<string>>;
};
const sortOptions = ["Populare", "Pret crescator", "Pret descrescator", "Noi"];

export default function Sortare({
  selectedSort,
  setSelectedSort,
  totalCount,
  tabel,
  id,
}: Types) {
  const [isSaved, setIsSaved] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  const categories = [
    { label: "Meeting Room", link: `/produse/${tabel}` },
    { label: "Beer Point", link: `/produse/${tabel}/inele` },
    { label: "Training Room 1", link: `/produse/${tabel}/cercei` },
    { label: "Training Room 2", link: `/produse/${tabel}/lanturi` },
    { label: "Useri", link: `/produse/${tabel}/bratari` },
  ];
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    } else {
      document.removeEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  return (
    <div className="w-full flex flex-wrap items-center justify-between lg:px-[50px]">
      {/* Left Side */}
      <div className="w-full">
        <h1 className="text-2xl font-bold">Cereri</h1>
        {/* <div className="flex justify-end w-full items-center gap-2 py-3">
          <span className="text-sm text-gray-700">
            Livrare în{" "}
            <span className="text-[#b5a798] cursor-pointer hover:underline">
              Moldova
            </span>
          </span>
        </div> */}

        {/* Filters */}
        <div className="flex justify-between items-center text-sm py-2">
          {/* <button className="flex items-center gap-2 px-3 py-1 rounded-full text-sm border bg-gray-100 hover:bg-gray-200">
            <Filter size={14} />
            <span>Filtru</span>
          </button> */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">
              {totalCount} rezultate
            </span>
            <div
              className="flex items-center gap-2 group cursor-pointer"
              onClick={() => setIsSaved((prev) => !prev)}
            >
              {/* <span className="bg-slate-100 p-2 rounded-full">
                {isSaved ? (
                  // ✅ Filled Heart
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="w-4 h-4 fill-[#b5a798]"
                    viewBox="0 0 24 24"
                  >
                    <path
                      d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 
                4.42 3 7.5 3c1.74 0 3.41 0.81 4.5 2.09C13.09 3.81 
                14.76 3 16.5 3 19.58 3 22 5.42 
                22 8.5c0 3.78-3.4 6.86-8.55 
                11.54L12 21.35z"
                    />
                  </svg>
                ) : (
                  // ❌ Outline Heart
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="w-4 h-4 fill-none stroke-[#b5a798]"
                    viewBox="0 0 24 24"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 
                  4.42 3 7.5 3c1.74 0 3.41 0.81 4.5 2.09C13.09 3.81 
                  14.76 3 16.5 3 19.58 3 22 5.42 
                  22 8.5c0 3.78-3.4 6.86-8.55 
                  11.54L12 21.35z"
                    />
                  </svg>
                )}
              </span> */}
              {/* <div className="text-[#b5a798] text-sm font-medium group-hover:underline">
                Salveaza
              </div> */}
            </div>
          </div>

          {/* Right Side */}
          <div className="flex items-center gap-2 relative whitespace-nowrap">
            <div className="relative" ref={dropdownRef}>
              {isOpen && (
                <ul className="absolute right-0 bg-white border shadow-lg rounded-md mt-2 z-[6]">
                  {sortOptions.map((option) => (
                    <li
                      key={option}
                      onClick={() => {
                        setSelectedSort(option);
                        setIsOpen(false);
                      }}
                      className={`px-4 py-2 text-sm cursor-pointer hover:bg-gray-100 ${
                        selectedSort === option ? "font-semibold" : ""
                      }`}
                    >
                      {option}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <button className="border p-2 rounded-full bg-gray-100 hover:bg-gray-200">
              <LayoutGrid size={14} />
            </button>
          </div>
        </div>
      </div>
      <div className="flex gap-2 sm:mt-0 overflow-scroll scrollbar-hide pb-3">
        {/* Filter Button styled like the rest */}
        <button className="px-3 py-1 rounded-full text-sm border bg-gray-100 hover:bg-gray-200 flex items-center gap-2">
          <Filter size={14} />
        </button>
        {/* Category Buttons */}
        {categories.map((filter, i) => (
          <Link key={i} href={filter.link}>
            <button
              className={`px-3 py-1 rounded-full text-sm border ${
                id && filter.label.toLowerCase() === id
                  ? "bg-gray-800 text-white"
                  : "bg-gray-100 hover:bg-gray-200"
              }
                  ${i !== categories.length - 1 ? "" : "mr-3"}
              `}
            >
              {filter.label}
            </button>
          </Link>
        ))}
      </div>
    </div>
  );
}
