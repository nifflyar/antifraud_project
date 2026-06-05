from app.domain.transaction.entity import Transaction
from app.domain.transaction.vo import TransactionId
from app.domain.upload.vo import UploadId
from app.domain.passenger.vo import PassengerId
from app.infrastructure.db.models.transaction import TransactionModel


class TransactionMapper:
    @staticmethod
    def to_domain(model: TransactionModel) -> Transaction:
        return Transaction(
            id=model.id,
            upload_id=model.upload_id,
            source=model.source,
            op_type=model.op_type,
            op_datetime=model.op_datetime,
            dep_datetime=model.dep_datetime,
            train_no=model.train_no,
            channel=model.channel,
            aggregator=model.aggregator,
            terminal=model.terminal,
            cashdesk=model.cashdesk,
            point_of_sale=model.point_of_sale,
            amount=model.amount,
            fee=model.fee,
            fio=model.fio,
            iin=model.iin,
            doc_no=model.doc_no,
            phone=model.phone,
            gender=model.gender,
            ticket_no=model.ticket_no,
            tariff_type=model.tariff_type,
            service_class=model.service_class,
            branch=model.branch,
            sale_user=model.sale_user,
            carrier=model.carrier,
            settlement_type=model.settlement_type,
            order_no=model.order_no,
            dep_station=model.dep_station,
            arr_station=model.arr_station,
            route=model.route,
            passenger_id=model.passenger_id,
        )

    @staticmethod
    def to_model(tx: Transaction) -> TransactionModel:
        return TransactionModel(
            id=tx.id,
            upload_id=tx.upload_id,
            source=tx.source,
            op_type=tx.op_type,
            op_datetime=tx.op_datetime,
            dep_datetime=tx.dep_datetime,
            train_no=tx.train_no,
            channel=tx.channel,
            aggregator=tx.aggregator,
            terminal=tx.terminal,
            cashdesk=tx.cashdesk,
            point_of_sale=tx.point_of_sale,
            amount=tx.amount,
            fee=tx.fee,
            fio=tx.fio,
            iin=tx.iin,
            doc_no=tx.doc_no,
            phone=tx.phone,
            gender=tx.gender,
            ticket_no=tx.ticket_no,
            tariff_type=tx.tariff_type,
            service_class=tx.service_class,
            branch=tx.branch,
            sale_user=tx.sale_user,
            carrier=tx.carrier,
            settlement_type=tx.settlement_type,
            order_no=tx.order_no,
            dep_station=tx.dep_station,
            arr_station=tx.arr_station,
            route=tx.route,
            passenger_id=tx.passenger_id,
        )
