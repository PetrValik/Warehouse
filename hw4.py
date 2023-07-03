import math
from typing import List, Dict, Set, Tuple, Optional

Move = Set[Tuple[str, int, int]]


class Package:
    def __init__(self, amount: int, price: int, expiry: str):
        self.amount = amount
        self.price = price
        self.expiry = expiry


class Movement:
    def __init__(self, item: str, amount: int, price: int, tag: str):
        self.item = item
        self.amount = amount
        self.price = price
        self.tag = tag


class Warehouse:
    def __init__(self) -> None:
        self.inventory: Dict[str, List[Package]] = {}
        self.history: List[Movement] = []

    def store(self, item: str, amount: int, price: int,
              expiry: str, tag: str) -> None:
        self.history.append(Movement(item, amount, price, tag))
        package_list = []

        if item in self.inventory:
            package_list = Warehouse.package_store(self, item, amount,
                                                   price, expiry)
        else:
            package_list.append(Package(amount, price, expiry))
        self.inventory[item] = package_list

    def package_store(self, item: str, amount: int,
                      price: int, expiry: str, ) -> List[Package]:
        items = self.inventory[item]
        package = Package(amount, price, expiry)

        for i in range(len(items)):
            if items[i].expiry <= expiry:
                items.insert(i, package)
                return items

        items.append(package)
        return items

    def find_inconsistencies(self) -> Move:
        inconsistencies: Move = set()
        inconsistencies = self.search_inventory(inconsistencies)
        inconsistencies = self.search_history(inconsistencies)
        inconsistencies = self.remove_empty_tags(inconsistencies)
        return inconsistencies

    def search_history(self, inconsistencies: Move) -> Move:

        for movement in self.history:
            was_find = False

            for item in inconsistencies:
                if movement.item == item[0] and movement.price == item[1]:
                    was_find = True
                    name, price, amount = item
                    inconsistencies.remove(item)
                    inconsistencies.add((name, price,
                                         amount - movement.amount))
                    break

            if not was_find:
                inconsistencies.add((movement.item,
                                     movement.price, -movement.amount))

        return inconsistencies

    def search_inventory(self, inconsistencies: Move) -> Move:
        for key in self.inventory:

            for package in self.inventory[key]:
                was_find = False

                for item in inconsistencies:

                    if key == item[0] and package.price == item[1]:
                        was_find = True
                        name, price, amount = item
                        inconsistencies.remove(item)
                        inconsistencies.add((name, price,
                                             amount + package.amount))
                        break

                if not was_find:
                    inconsistencies.add((key, package.price, package.amount))

        return inconsistencies

    def remove_empty_tags(self, inconsistencies: Move) -> Move:
        list_inconsistencies = list(inconsistencies)

        for i in range(len(inconsistencies) - 1, -1, -1):

            if list_inconsistencies[i][2] == 0:
                list_inconsistencies.pop(i)

        return set(list_inconsistencies)

    def remove_expired(self, expired: str) -> List[Package]:
        expired_products = []

        for key in self.inventory:

            for i in range(len(self.inventory[key]) - 1, - 1, - 1):
                package = self.inventory[key][i]

                if package.expiry < expired:
                    self.history.append(Movement(key, -package.amount,
                                                 package.price, "EXPIRED"))
                    expired_products.append(package)
                    self.inventory[key].remove(package)

        return expired_products

    def try_sell(self, item: str, amount: int,
                 price: int, tag: str) -> Tuple[int, int]:
        already_sell = 0
        price_amount = 0, 0
        sold: List[Package] = []
        paid = 0

        if item not in self.inventory:
            return already_sell, paid

        paid, already_sell, last_sold, sold = \
            self.packages_to_sell(item, amount,
                                  paid, already_sell, sold)

        if paid / already_sell <= price:
            return self.sell(sold, last_sold, item, tag,
                             already_sell, paid)

        if last_sold is None:
            last_sold = sold[-1], sold[-1].amount

        for i in range(len(sold) - 1, -1, -1):

            if paid / already_sell <= price:
                return self.sell(sold, last_sold, item, tag,
                                 already_sell, paid)

            already_sell -= last_sold[1]
            paid -= last_sold[1] * last_sold[0].price

            if paid == 0 or paid / already_sell < price:
                last_sold = self.max_sell(paid, already_sell,
                                          last_sold, price, sold)
                if last_sold is None:

                    if sold is None:
                        return price_amount
                    return self.sell(sold, last_sold, item, tag,
                                     already_sell, paid)

                paid += last_sold[1] * last_sold[0].price
                already_sell += last_sold[1]
                return self.sell(sold, last_sold, item, tag,
                                 already_sell, paid)

            if i - 1 >= 0:
                last_sold = sold[i - 1], sold[i - 1].amount
            sold.pop()

        return price_amount

    def packages_to_sell(self, item: str, amount: int, paid: int,
                         already_sell: int, sold: List[Package]) \
            -> Tuple[int, int, Optional[Tuple[Package, int]], List[Package]]:
        partly_sold = None
        for i in range(len(self.inventory[item]) - 1, -1, -1):
            package = self.inventory[item][i]

            if amount - already_sell >= package.amount:
                paid += package.amount * package.price
                sold.append(package)
                already_sell += package.amount

            else:
                paid += (amount - already_sell) * package.price
                sold.append(package)
                partly_sold = (package, amount - already_sell)
                already_sell = amount
                break

        return paid, already_sell, partly_sold, sold

    def max_sell(self, paid: int, already_sell: int,
                 last_item: Tuple[Package, int], price: int,
                 sold: List[Package]) -> Optional[Tuple[Package, int]]:
        middle_find = False
        min_sold = 1
        max_sold = last_item[1]

        if ((min_sold * last_item[0].price) + paid) / \
                (already_sell + 1) > price:
            sold.pop()
            return None

        while not middle_find:
            middle = (max_sold + min_sold) // 2

            if ((middle * last_item[0].price) + paid) / \
                    (already_sell + middle) > price:
                max_sold = middle

                if (((max_sold * last_item[0].price) - last_item[0].price)
                        + paid) / (already_sell + max_sold - 1) < price:
                    return last_item[0], max_sold - 1

            else:
                min_sold = middle
                if (((min_sold * last_item[0].price) + last_item[0].price)
                        + paid) / (already_sell + min_sold + 1) > price:
                    break

        return last_item[0], min_sold

    def sell(self, sold: List[Package],
             partly_sold: Optional[Tuple[Package, int]],
             item: str,
             tag: str,
             already_sell: int,
             paid: int) -> Tuple[int, int]:
        counter = 0

        for i in range(len(self.inventory[item]) - 1, -1, -1):

            if counter == len(sold):
                break

            package = self.inventory[item][i]

            if partly_sold is not None and package == partly_sold[0]:

                if partly_sold[1] != 0:
                    self.history.append(Movement(item, -partly_sold[1],
                                                 package.price, tag))
                    package.amount = package.amount - partly_sold[1]

            else:
                self.history.append(Movement(item, -package.amount,
                                             package.price, tag))
                self.inventory[item].remove(package)
            counter += 1

        for i in range(len(self.inventory[item]) - 1, -1, -1):
            package = self.inventory[item][i]

            if package.amount == 0:
                self.inventory[item].remove(package)

        return already_sell, paid

    def average_prices(self) -> Dict[str, float]:
        average_prices = {}

        for key in self.inventory:
            price = 0
            amount = 0

            for package in self.inventory[key]:
                price += package.price * package.amount
                amount += package.amount

            if amount != 0 and price != 0:
                average_prices[key] = price / amount

        return average_prices

    def best_suppliers(self) -> Set[str]:
        suppliers: Dict[str, Dict[str, int]] = {}

        for movement in self.history:

            if movement.amount > 0:

                if movement.item not in suppliers.keys():
                    suppliers[movement.item] = {}

                if movement.tag not in suppliers[movement.item].keys():
                    suppliers[movement.item][movement.tag] = movement.amount

                suppliers[movement.item][movement.tag] += movement.amount

        best_suppliers = set()

        for key in suppliers:
            best_suppliers.update(self.best_item_supplier(suppliers[key]))

        return best_suppliers

    def best_item_supplier(self, suppliers: Dict[str, int]) -> Set[str]:
        best_supplier: Set[str] = set()
        best_supplier_amount = 0

        for key in suppliers:

            if suppliers[key] > best_supplier_amount:
                best_supplier_amount = suppliers[key]
                best_supplier.clear()
                best_supplier.add(key)

            elif suppliers[key] == best_supplier_amount:
                best_supplier.add(key)

        return best_supplier


def print_warehouse(warehouse: Warehouse) -> None:
    print("===== INVENTORY =====", end="")
    for item, pkgs in warehouse.inventory.items():
        print(f"\n* Item: {item}")
        print("    amount  price  expiration date")
        print("  ---------------------------------")
        for pkg in pkgs:
            print(f"     {pkg.amount:4d}   {pkg.price:4d}     {pkg.expiry}")
    print("\n===== HISTORY ======")
    print("    item     amount  price   tag")
    print("-------------------------------------------")
    for mov in warehouse.history:
        print(f" {mov.item:^11}   {mov.amount:4d}   "
              f"{mov.price:4d}   {mov.tag}")


def example_warehouse() -> Warehouse:
    wh = Warehouse()

    wh.store("rice", 100, 17, "20220202", "ACME Rice Ltd.")
    wh.store("corn", 70, 15, "20220315", "UniCORN & co.")
    wh.store("rice", 200, 158, "20771023", "RICE Unlimited")
    wh.store("peas", 9774, 1, "20220921", "G. P. a C.")
    wh.store("rice", 90, 14, "20220202", "Theorem's Rice")
    wh.store("peas", 64, 7, "20211101", "Discount Peas")
    wh.store("rice", 42, 9, "20211111", "ACME Rice Ltd.")

    return wh


def test1() -> None:
    wh = example_warehouse()

    for item, length in ('rice', 4), ('peas', 2), ('corn', 1):
        assert item in wh.inventory
        assert len(wh.inventory[item]) == length

    assert len(wh.history) == 7

    # uncomment to visually check the output:
    # print_warehouse(wh)


def test2() -> None:
    wh = example_warehouse()
    assert wh.find_inconsistencies() == set()

    wh.inventory['peas'][0].amount = 9773
    wh.history[4].price = 12

    assert wh.find_inconsistencies() == {
        ('peas', 1, -1),
        ('rice', 14, 90),
        ('rice', 12, -90),
    }


def test3() -> None:
    wh = example_warehouse()
    bad_peas = wh.inventory['peas'][-1]
    assert wh.remove_expired('20211111') == [bad_peas]
    assert len(wh.history) == 8
    mov = wh.history[-1]
    assert mov.item == 'peas'
    assert mov.amount == -64
    assert mov.price == 7
    assert mov.tag == 'EXPIRED'

    assert len(wh.inventory['peas']) == 1


def test4() -> None:
    wh = example_warehouse()
    assert wh.try_sell('rice', 500, 9, 'Pear Shop') == (42, 42 * 9)
    assert len(wh.history) == 8
    assert wh.find_inconsistencies() == set()

    wh = example_warehouse()
    assert wh.try_sell('rice', 500, 12, 'Pear Shop') \
           == (42 + 25, 42 * 9 + 25 * 17)
    assert len(wh.history) == 9
    assert wh.find_inconsistencies() == set()

    wh = example_warehouse()
    assert wh.try_sell('rice', 500, 14, 'Pear Shop') \
           == (42 + 70, 42 * 9 + 70 * 17)
    assert len(wh.history) == 9
    assert wh.find_inconsistencies() == set()

    wh = example_warehouse()
    assert wh.try_sell('rice', 500, 15, 'Pear Shop') \
           == (42 + 100 + 90, 42 * 9 + 100 * 17 + 90 * 14)
    assert len(wh.history) == 10
    assert wh.find_inconsistencies() == set()

    wh = example_warehouse()
    assert wh.try_sell('rice', 500, 16, 'Pear Shop') \
           == (42 + 100 + 90 + 2, 42 * 9 + 100 * 17 + 90 * 14 + 2 * 158)
    assert len(wh.history) == 11
    assert wh.find_inconsistencies() == set()

    # uncomment to visually check the output:
    # print_warehouse(wh)

    wh = example_warehouse()
    assert wh.try_sell('rice', 500, 81, 'Pear Shop') \
           == (42 + 100 + 90 + 200, 42 * 9 + 100 * 17 + 90 * 14 + 200 * 158)
    assert len(wh.history) == 11
    assert wh.find_inconsistencies() == set()


def test5() -> None:
    wh = example_warehouse()

    expected = {
        'rice': 80.875,
        'corn': 15,
        'peas': (9774 + 64 * 7) / (9774 + 64),
    }

    avg_prices = wh.average_prices()

    assert expected.keys() == avg_prices.keys()

    for item in avg_prices:
        assert math.isclose(avg_prices[item], expected[item])

    assert wh.best_suppliers() \
           == {'UniCORN & co.', 'G. P. a C.', 'RICE Unlimited'}


if __name__ == '__main__':
    # print_warehouse(example_warehouse())
    test1()
    test2()
    test3()
    test4()
    test5()
